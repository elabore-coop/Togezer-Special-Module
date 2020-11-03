from datetime import datetime
import pytz
from odoo import models, fields, api
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT

from .common import IMAGE_PLACEHOLDER, DEFAULT_MESSAGE_PREVIEW_LENGTH, MONTHS

TREE_TEMPLATE = '<table style="width: 100%%; border: none;" title="Conversation">' \
                '<tbody>' \
                '<tr>' \
                '<td style="width: 99%%;">' \
                '<table style="width: 100%%; border: none;">' \
                '<tbody>' \
                '<tr>' \
                '<span id="subject">%s</span></td>' \
                '<td id="date" style="text-align: right;" title="%s">%s</td>' \
                '</tr>' \
                '<tr>' \
                '<td><p id="notifications" style="font-size: x-small;"><strong>%s</strong></p></td>' \
                '<td id="participants" style="text-align: right;">%s</td>' \
                '</tr>' \
                '</tbody>' \
                '</table>' \
                '%s' \
                '</td>' \
                '</tr>' \
                '</tbody>' \
                '</table>'



class Conversation(models.Model):
    _inherit = ['mail.thread']

    # -- Get HTML view for Tree View
    @api.depends('name')
    def _subject_display(self):

        # Get preview length. Will use it for message body preview
        body_preview_length = int(self.env['ir.config_parameter'].sudo().get_param('cetmix.messages_easy_text_preview',
                                                                                   DEFAULT_MESSAGE_PREVIEW_LENGTH))

        # Get current timezone
        tz = self.env.user.tz
        if tz:
            local_tz = pytz.timezone(tz)
        else:
            local_tz = pytz.utc

        # Get current time
        now = datetime.now(local_tz)
        # Compose subject
        for rec in self.with_context(bin_size=False):
            # Get message date with timezone
            message_date = pytz.utc.localize(rec.last_message_post).astimezone(local_tz)
            if rec.last_message_post:
                # Compose displayed date/time
                days_diff = (now.date() - message_date.date()).days
                if days_diff == 0:
                    date_display = datetime.strftime(message_date, '%H:%M')
                elif days_diff == 1:
                    date_display = "%s %s" % (_("Yesterday"), datetime.strftime(message_date, '%H:%M'))
                elif now.year == message_date.year:
                    date_display = "%s %s" % (str(message_date.day), _(MONTHS.get(message_date.month)))
                else:
                    date_display = str(message_date.date())
            else:
                date_display = ""

            # Compose messages count
            message_count_text = ''
            message_count = rec.message_count
            # Total messages
            if message_count == 0:
                message_count_text = _("No messages")
            else:
                message_count_text = "%s %s" % (
                    str(message_count), _("message") if message_count == 1 else _("messages"))
                # New messages
                message_needaction_count = rec.message_needaction_count
                if message_needaction_count > 0:
                    message_count_text = "%s, %s %s" % (message_count_text, str(message_needaction_count), _("new"))

            # Participants
            participant_text = ''
            for participant in rec.partner_ids:
                participant_text = "%s %s" % (participant_text,
                                              '<img class="rounded-circle" style="width:24px;max-height:24px;margin:2px;" title="%s" src="data:image/png;base64, %s"/>' % (
                                                  sanitize_name(participant.name),
                                                  participant.image_128.decode(
                                                      'utf-8') if participant.image_128 else IMAGE_PLACEHOLDER))
            # Compose preview body
            plain_body = ''
            for message in rec.message_ids:
                if message.message_type != 'notification':
                    message_body = message.body
                    if len(message_body) > body_preview_length:
                        message_body = "%s..." % message_body[:body_preview_length]
                    plain_body = '<img class="rounded-circle" style="width:16px;max-height:16px;margin:2px;" title="%s" src="data:image/png;base64, %s"/> <span id="text-preview" style="color:#808080;vertical-align:middle;">%s</p>' % (
                        sanitize_name(message.author_id.name) if message.author_id else "",
                        message.author_avatar.decode('utf-8') if message.author_avatar else IMAGE_PLACEHOLDER,
                        html2plaintext(message_body))
                    break

            rec.subject_display = TREE_TEMPLATE % (
#                rec.author_id.image_128.decode('utf-8') if rec.author_id and rec.author_id.image_128 else IMAGE_PLACEHOLDER,
#                sanitize_name(rec.author_id.name) if rec.author_id else "",
#                rec.author_id.name if rec.author_id else "",
                rec.name if rec.name else '',
                str(message_date.replace(tzinfo=None)) if rec.last_message_post else "",
                date_display,
                message_count_text,
                participant_text,
                plain_body
            )