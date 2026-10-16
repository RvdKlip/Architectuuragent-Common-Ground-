"""Nieuwe Confluence Cloud-pagina na expliciete review en publicatieactie."""
import base64
import json
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .output import report_html


class ConfluencePublishError(RuntimeError):
    pass


def cloud_base(value):
    url = urlsplit(value.strip())
    if (url.scheme != 'https' or not url.hostname or not url.hostname.endswith('.atlassian.net')
            or url.username or url.password or url.port not in (None, 443)
            or url.path.rstrip('/') not in ('', '/wiki') or url.query or url.fragment):
        raise ValueError('Gebruik de HTTPS-basis-URL van je Confluence Cloud-omgeving (*.atlassian.net).')
    return 'https://'+url.hostname


def publish_plan(plan, sources, brand, base_url, email, token, space_id, parent_id=''):
    base = cloud_base(base_url)
    if not email.strip() or not token.strip() or any(c in email+token for c in '\r\n'):
        raise ValueError('Stel een Confluence-account en API-token veilig in.')
    if not str(space_id).isdigit() or (parent_id and not str(parent_id).isdigit()):
        raise ValueError('Gebruik numerieke Confluence space-ID en eventuele parent-ID.')
    html = report_html(plan, sources, brand, confluence=True)
    payload = {'spaceId': str(space_id), 'status': 'current', 'title': plan['title']+' — CONCEPT',
               'body': {'representation': 'storage', 'value': html}}
    if parent_id:
        payload['parentId'] = str(parent_id)
    authentication = base64.b64encode((email.strip()+':'+token.strip()).encode()).decode()
    request = Request(base+'/wiki/api/v2/pages', data=json.dumps(payload).encode(), method='POST',
                      headers={'Authorization': 'Basic '+authentication, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=30) as response:
            page = json.load(response)
    except HTTPError as error:
        raise ConfluencePublishError(f'Confluence gaf HTTP {error.code}. Controleer rechten en de doelpagina voordat je opnieuw publiceert.') from None
    except (URLError, OSError, ValueError):
        raise ConfluencePublishError('Geen publicatiebevestiging ontvangen. Controleer Confluence voordat je opnieuw publiceert; de pagina kan al zijn aangemaakt.') from None
    if not page.get('id'):
        raise ConfluencePublishError('Geen geldige paginabevestiging ontvangen; controleer Confluence voordat je opnieuw publiceert.')
    return {'id': str(page['id']), 'url': base+'/wiki/pages/viewpage.action?pageId='+str(page['id'])}
