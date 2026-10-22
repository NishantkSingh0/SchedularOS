"""
WhatsApp Webhook Handler
Handles inbound WhatsApp messages and triggers conversation agent
"""
import json
import os
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings


def _find_lead_by_phone(from_number):
    """Find a lead whose phone matches the WhatsApp sender number."""
    from core.models import Lead

    digits = "".join(ch for ch in (from_number or "") if ch.isdigit())
    if not digits:
        return None

    lead = Lead.objects.filter(phone=from_number).first()
    if lead:
        return lead

    # Fall back to matching on the trailing digits (handles +/country-code diffs)
    for tail in (digits[-10:], digits[-9:], digits[-8:]):
        if not tail:
            continue
        lead = Lead.objects.filter(phone__endswith=tail).first()
        if lead:
            return lead
    return None


def _store_inbound_message(lead, from_number, message_id, message_text):
    """Store the inbound WhatsApp message; returns (conversation, created)."""
    from core.models import Conversation, Message

    if message_id and Message.objects.filter(external_id=message_id).exists():
        return None, False  # duplicate webhook delivery

    conversation = Conversation.objects.filter(
        lead=lead, channel='whatsapp'
    ).order_by('-created_at').first()
    if not conversation:
        conversation = Conversation.objects.create(
            org=lead.org, lead=lead, channel='whatsapp'
        )

    Message.objects.create(
        conversation=conversation,
        direction='inbound',
        body=message_text or '',
        external_id=message_id or '',
    )
    return conversation, True


def _trigger_conversation_agent(lead):
    """Kick off a workflow with a single conversation step for this lead."""
    from orchestration.engine import create_workflow

    return create_workflow(
        org=lead.org,
        goal="Respond to inbound WhatsApp message",
        steps=[{"agent": "conversation", "delay_minutes": 0}],
        lead=lead,
    )


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle WhatsApp webhook events

    - Messages from users
    - Delivery receipts
    - Message status updates
    """
    try:
        data = json.loads(request.body)
        processed = []

        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') != 'messages':
                    continue
                value = change.get('value', {})
                for msg in value.get('messages', []):
                    from_number = msg.get('from')
                    message_id = msg.get('id')
                    message_text = msg.get('text', {}).get('body', '')

                    lead = _find_lead_by_phone(from_number)
                    if not lead:
                        processed.append({"from": from_number, "status": "no_lead"})
                        continue

                    conversation, created = _store_inbound_message(
                        lead, from_number, message_id, message_text
                    )
                    if not created:
                        processed.append({"from": from_number, "status": "duplicate"})
                        continue

                    run = _trigger_conversation_agent(lead)
                    processed.append({
                        "from": from_number,
                        "status": "queued",
                        "workflow_id": str(run.id),
                    })

        return JsonResponse({'status': 'success', 'processed': processed})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def whatsapp_verify(request):
    """
    Verify WhatsApp webhook during setup
    """
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')

    if mode == 'subscribe' and token == os.getenv('WHATSAPP_VERIFY_TOKEN', 'test_token'):
        return HttpResponse(challenge, content_type='text/plain')

    return HttpResponseForbidden()
