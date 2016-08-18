from django.http import HttpResponse
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from frontend.models import Chemical, Prescription
from frontend.models import Practice, SHA, PCT, Section
from frontend.models import Measure
from frontend.models import OrgBookmark
from frontend.forms import OrgBookmarkForm
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from allauth.account.utils import perform_login
from allauth.account import app_settings


##################################################
# BNF SECTIONS
##################################################
def all_bnf(request):
    sections = Section.objects.all()
    context = {
        'sections': sections
    }
    return render(request, 'all_bnf.html', context)


def bnf_section(request, section_id):
    section = get_object_or_404(Section, bnf_id=section_id)
    id_len = len(section_id)
    bnf_chapter = None
    bnf_section = None
    try:
        if id_len > 2:
            bnf_chapter = Section.objects.get(bnf_id=section_id[:2])
        if id_len > 4:
            bnf_section = Section.objects.get(bnf_id=section_id[:4])
    except Section.DoesNotExist:
        pass
    chemicals = None
    subsections = Section.objects.filter(
        bnf_id__startswith=section_id) \
        .extra(where=["CHAR_LENGTH(bnf_id)=%s" % (id_len + 2)])
    if not subsections:
        chemicals = Chemical.objects.filter(bnf_code__startswith=section_id) \
                            .order_by('chem_name')
    context = {
        'section': section,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'subsections': subsections,
        'chemicals': chemicals,
        'page_id': section_id
    }
    return render(request, 'bnf_section.html', context)


##################################################
# CHEMICALS
##################################################

def all_chemicals(request):
    chemicals = Chemical.objects.all().order_by('bnf_code')
    context = {
        'chemicals': chemicals
    }
    return render(request, 'all_chemicals.html', context)


def chemical(request, bnf_code):
    c = get_object_or_404(Chemical, bnf_code=bnf_code)

    # Get BNF chapter, section etc.
    bnf_chapter = Section.objects.get(bnf_id=bnf_code[:2])
    bnf_section = Section.objects.get(bnf_id=bnf_code[:4])
    try:
        bnf_para = Section.objects.get(bnf_id=bnf_code[:6])
    except Section.DoesNotExist:
        bnf_para = None

    context = {
        'page_id': bnf_code,
        'chemical': c,
        'bnf_chapter': bnf_chapter,
        'bnf_section': bnf_section,
        'bnf_para': bnf_para
    }
    return render(request, 'chemical.html', context)


##################################################
# GP PRACTICES
##################################################

def all_practices(request):
    practices = Practice.objects.filter(setting=4).order_by('name')
    context = {
        'practices': practices
    }
    return render(request, 'all_practices.html', context)


##################################################
# AREA TEAMS
##################################################

def all_area_teams(request):
    area_teams = SHA.objects.all().order_by('code')
    context = {
        'area_teams': area_teams
    }
    return render(request, 'all_area_teams.html', context)


def area_team(request, at_code):
    requested_at = get_object_or_404(SHA, code=at_code)
    prescriptions = Prescription.objects.filter(sha=requested_at)
    num_prescriptions = prescriptions.count()
    prescriptions_to_return = prescriptions[:100]
    context = {
        'area_team': requested_at,
        'num_prescriptions': num_prescriptions,
        'prescriptions': prescriptions_to_return
    }
    return render(request, 'area_team.html', context)


##################################################
# CCGs
##################################################

def all_ccgs(request):
    ccgs = PCT.objects.filter(org_type="CCG").order_by('name')
    context = {
        'ccgs': ccgs
    }
    return render(request, 'all_ccgs.html', context)


##################################################
# MEASURES
# These replace old CCG and practice dashboards.
##################################################

def all_measures(request):
    measures = Measure.objects.all().order_by('name')
    context = {
        'measures': measures
    }
    return render(request, 'all_measures.html', context)


def measure_for_all_ccgs(request, measure):
    measure = get_object_or_404(Measure, id=measure)
    context = {
        'measure': measure
    }
    return render(request, 'measure_for_all_ccgs.html', context)


def measure_for_practices_in_ccg(request, ccg_code, measure):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    measure = get_object_or_404(Measure, id=measure)
    practices = Practice.objects.filter(ccg=requested_ccg)\
        .filter(setting=4).order_by('name')
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code,
        'measure': measure
    }
    return render(request, 'measure_for_practices_in_ccg.html', context)


def measures_for_one_ccg(request, ccg_code):
    requested_ccg = get_object_or_404(PCT, code=ccg_code)
    if request.method == 'POST':
        form = OrgBookmarkForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            pct = form.cleaned_data['pct']
            try:
                user = User.objects.create_user(
                    username=email, email=email)
            except IntegrityError:
                user = User.objects.get(username=email)
                messages.success(
                    request,
                    "Thanks, you're now subscribed to monthly "
                    "alerts about this practice")
            user = authenticate(key=user.profile.key)
            OrgBookmark.objects.get_or_create(
                user=user,
                pct=pct, include_in_email=True
            )
            return perform_login(
                request, user,
                app_settings.EmailVerificationMethod.MANDATORY,
                signup=True)


    else:
        form = OrgBookmarkForm(
            initial={'pct': requested_ccg.pk, 'next': request.path})
    # XXX test if they're already signed up and don't show the form if not
    if request.user.is_authenticated():
        signed_up_for_alert = request.user.orgbookmark_set.filter(
            pct=requested_ccg)
    else:
        signed_up_for_alert = False
    practices = Practice.objects.filter(
        ccg=requested_ccg).filter(
            setting=4).order_by('name')
    context = {
        'ccg': requested_ccg,
        'practices': practices,
        'page_id': ccg_code,
        'form': form,
        'signed_up_for_alert': signed_up_for_alert
    }
    return render(request, 'measures_for_one_ccg.html', context)


def last_bookmark(request):
    """Redirect the logged in user to the CCG they last bookmarked, or if
    they're not logged in, just go straight to the homepage -- both
    with a message.

    """
    if request.user.is_authenticated():
        ccg = request.user.orgbookmark_set.last().pct
        messages.success(
            request,
            "Thanks, you're now subscribed to monthly "
            "alerts about this practice")
        return redirect('measures_for_one_ccg', ccg_code=ccg.code)
    else:
        messages.success("Thanks, you're now subscribed to monthly alerts")
        return redirect('home')


def measures_for_one_practice(request, code):
    p = get_object_or_404(Practice, code=code)
    context = {
        'practice': p,
        'page_id': code
    }
    return render(request, 'measures_for_one_practice.html', context)


##################################################
# TEST HTTP CODES
##################################################
def test_500_view(request):
    return HttpResponse(status=500)
