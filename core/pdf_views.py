from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .models import BucketList

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

class ExportListPDFView(View):
    def get(self, request, pk):
        bucket = get_object_or_404(BucketList, id=pk)
        # Check access (same as detail view)
        is_owner = bucket.owner == request.user
        is_shared = request.user.is_authenticated and request.user in bucket.shared_with.all()
        if not (is_owner or is_shared or bucket.is_public):
            return HttpResponseForbidden("Zugriff verweigert.")
            
        context = {
            'bucket': bucket,
            'items': bucket.items.all(),
            'template_config': bucket.category.template
        }
        
        response = render_to_pdf('core/pdf_export.html', context)
        if response:
            filename = f"{bucket.title}.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Fehler bei der PDF-Generierung", status=500)
