from django.template import RequestContext, loader
from comics.models import Comics, ComicsForm
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

# Create your views here.
def index(request):
    class NoComics:
        def __init__(self,cid):
	    self.cid=cid
	fake=True
    br=20
    if request.user.is_authenticated():
        tmp_comics_list = Comics.objects.order_by('cid')
        last_id= Comics.objects.order_by('-cid')[0].cid
    else:
        tmp_comics_list = Comics.objects.filter(visible=True).order_by('cid')
        last_id= Comics.objects.filter(visible=True).order_by('-cid')[0].cid
    comics_list=[NoComics(i) for i in xrange(1,last_id+1)]
    for comics in tmp_comics_list:
	comics_list[comics.cid-1]=comics
    for i in xrange(br-1,len(comics_list),br):
	comics_list[i].br=True
    return render_to_response('comics/index.html',
                              {'comics_list': comics_list},
                              context_instance=RequestContext(request))


def index_thumbnail(request):
    if request.user.is_authenticated():
        comics_list=Comics.objects.order_by('-cid')
    else:
        comics_list=Comics.objects.filter(visible=True).order_by('-cid')
        
    return render_to_response('comics/index_thumbnail.html',
                              {'comics_list': comics_list},
                              context_instance=RequestContext(request))

def detail(request, comics_id):
    comics_id=int(comics_id)
    this = get_object_or_404(Comics,cid=comics_id,visible=True)
    if this.author == request.user and request.POST.has_key('code'):
            return HttpResponseRedirect(this.get_absolute_url()+'?code')
    first = Comics.objects.filter(visible=True).order_by('cid')[0]
    last = Comics.objects.filter(visible=True).order_by('-cid')[0]
    try:
        prev = Comics.objects.filter(visible=True,cid__lt=comics_id).\
            order_by('-cid')[0]
    except IndexError:
        prev = None
    try:
        next = Comics.objects.filter(visible=True,cid__gt=comics_id).\
            order_by('cid')[0]
    except IndexError:
        next = None

    random = reverse('comics.views.random', args=(comics_id,))

    return render_to_response('comics/detail.html',
                              {'comics': this,
                               'first': first,
                               'last': last,
                               'prev': prev,
                               'next': next,
                               'code': True if request.GET.has_key('code')\
                                   and this.author == request.user else False,
                               'random': random},
                               context_instance=RequestContext(request))

def detail_unpublished(request, comics_id, timestamp):
    comics_id=int(comics_id)
    this = get_object_or_404(Comics,visible=False,cid=comics_id)
    if this.author == request.user:
        if request.POST.has_key('no'):
            return HttpResponseRedirect(this.get_absolute_url())
        elif request.POST.has_key('publish'):
            return HttpResponseRedirect(this.get_absolute_url()+'?publish')
    if this.pub_date.strftime('%s')!=timestamp:
        raise Http404
    return render_to_response('comics/detail_unpublished.html',
                              {'comics': this,
                               'publish': True if \
                                   request.GET.has_key('publish') \
                                   else False},
                              context_instance=RequestContext(request))

def random(request,comics_id=-1):
    try:
        random = Comics.objects.filter(visible=True).exclude(cid=comics_id).\
            order_by('?')[0]
        return HttpResponseRedirect(random.get_absolute_url())
    except IndexError:
        raise Http404


#Auth users methods

@login_required
def index_unpublished(request):
    comics_list=Comics.objects.filter(visible=False).order_by('pub_date')
    return render_to_response('comics/index_unpublished.html',
                              {'comics_list': comics_list},
                              context_instance=RequestContext(request))
    
@login_required
def edit(request, comics_id):
    comics_id=int(comics_id)
    this = get_object_or_404(Comics, cid=comics_id)
    try:
        if request.user != this.author:
            raise Http404
        elif request.POST.has_key('edit'):
            return HttpResponseRedirect(reverse(edit, args=(this.cid,)))
        elif request.POST.has_key('publish'):
            this.visible = True
            this.save()
            return HttpResponseRedirect(this.get_absolute_url()+'?code')
        elif request.method == 'POST':
            form = ComicsForm(request.POST, request.FILES, instance=this)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse(index_unpublished))
        else:
            form = ComicsForm(instance = this)
    except IntegrityError:
        error = 'exists'
    else:
        error = None
    return render_to_response('comics/edit_form.html',
                              {'comics': this,
                               'error': error,
                               'form': form},
                              context_instance=RequestContext(request))

@login_required
def add(request):
    if request.method == 'POST':
        this = Comics(author=request.user)
        form = ComicsForm(request.POST, request.FILES, instance=this)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(index_unpublished))
    else:            
        form = ComicsForm()
    return render_to_response('comics/edit_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))


