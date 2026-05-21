import os
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import get_template
from django.conf import settings
from django.contrib.staticfiles import finders
from xhtml2pdf import pisa
from io import BytesIO
from .models import BucketList

def link_callback(uri, rel):
    """
    Convert HTML images/stylesheets with relative paths to absolute filesystem paths
    so xhtml2pdf can load them from disk.
    """
    # use finders to find static files in development/production
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        return result[0]
        
    # fallback to static/media roots
    sUrl = settings.STATIC_URL      # e.g. 'static/' or '/static/'
    sRoot = str(settings.STATIC_ROOT)    # e.g. '/workspace/staticfiles/'
    mUrl = settings.MEDIA_URL
    mRoot = str(settings.MEDIA_ROOT)

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl) or '/static/' in uri:
        clean_uri = uri.split('/static/')[-1]
        path = os.path.join(sRoot, clean_uri)
    else:
        # Check in local static directories directly
        for static_dir in settings.STATICFILES_DIRS:
            test_path = os.path.join(str(static_dir), uri)
            if os.path.isfile(test_path):
                return test_path
        return uri

    # make sure that file exists
    if not os.path.isfile(path):
        return uri
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

class ExportListPDFView(View):
    def get(self, request, pk):
        bucket = get_object_or_404(BucketList, id=pk)
        # Check access
        is_owner = bucket.owner == request.user
        is_shared = request.user.is_authenticated and request.user in bucket.shared_with.all()
        if not (is_owner or is_shared or bucket.is_public):
            return HttpResponseForbidden("Zugriff verweigert.")
            
        context = {
            'bucket': bucket,
            'items': bucket.items.all(),
            'template_config': bucket.category.template
        }
        from django.shortcuts import render
        return render(request, 'core/pdf_export.html', context)
