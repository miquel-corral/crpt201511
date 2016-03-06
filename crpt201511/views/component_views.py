from __future__ import division

from threading import Thread

import math

from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext, loader
from django.views.decorators.csrf import ensure_csrf_cookie


from crpt201511.utils.assessment_utils import *
from crpt201511.utils.user_utils import *

from crpt201511.constants import *
from crpt201511.models import *
from crpt201511.settings import CRPT_URL
from crpt201511.trace import *
from crpt201511.utils.env_utils import *
from crpt201511.utils.component_question_utils import *
from crpt201511.forms import *
from crpt201511.utils.form_utils import *
from crpt201511.my_ftp import MyFTP
from crpt201511.utils.mail_utils import send_comments_email
from crpt201511.signals.my_signals import *


@ensure_csrf_cookie
@login_required
def component(request, assessment_id, component_id=None, subcomponent_id=None, third_component_id=None):
    """
    View for component of indicators form

    :param request:
    :param assessment_id: assessment id
    :param component_id: component id
    :param subcomponent_id: subcomponent id
    :param third_component_id: third_component id
    :return:
    """
    try:
        left_elements = None
        """
        print("--INITIAL PARAMS. START --")

        if component_id:
            print("component_id: " + str(component_id))
        if subcomponent_id:
            print("subcomponent_id: " + str(subcomponent_id))
        if third_component_id:
            print("third_component_id: " + str(third_component_id))

        print("--INITIAL PARAMS. END --")
        """
        # get username from session
        person = get_person(request)
        # get assessment
        assessment = Assessment.objects.get(id=assessment_id)
        # check person has rights for the assessment. TODO: Constants
        if not check_person_access_to_assessment(assessment, person):
            print("assessment: " + assessment.name)
            raise Exception('User has no permission to access this assessment')

        # get component
        if component_id:
            component = Component.objects.get(id=component_id)
        else:
            component = Component.objects.all().order_by('order')[:1].get()

        # elements of menu
        menu_elements = Component.objects.filter(parent=None).order_by('order')

        # TODO: review data_loader to assign parent properly

        # adjustment of horizontal menu
        menu_horizontal_elem_width = math.floor(100/len(menu_elements))

        # get subcomponent
        if subcomponent_id:
            subcomponent = Component.objects.get(id=subcomponent_id)
        else:
            try:
                subcomponent = Component.objects.filter(parent=component).order_by('order')[:1].get()
            except:
                subcomponent = None

        # elements of left menu
        if component:
            left_elements = Component.objects.filter(parent_id=component.id).order_by('order')

        # third level of hierarchy
        if third_component_id:
            third_component = Component.objects.get(id=third_component_id)
        else:
            try:
                third_component = Component.objects.filter(parent=subcomponent).order_by('order')[:1].get()
            except:
                third_component = None

        """
        print("--CHECK PARAMS. START --")

        print("component_id: " + str(component.id))
        print("subcomponent_id: " + str(subcomponent.id))
        print("thirdcomponent_id: " + str(third_component.id))

        print("--CHECK PARAMS. END --")
        """


        # considerations at component and subcomponent level
        considerations = ComponentConsideration.objects.filter(element=component).order_by('id')
        if subcomponent:
            # concatenate querysets same type
            considerations = considerations | ComponentConsideration.objects.filter(element=subcomponent).\
                order_by('id')
            if third_component:
                considerations = considerations | ComponentConsideration.objects.filter(element=third_component)


        # comments
        # TODO: create assessment components and change coding
        if third_component:
            comments = AssessmentComponentComment.objects.filter(element=third_component, assessment=assessment).\
                order_by('date_created')
        else:
            if subcomponent:
                comments = AssessmentComponentComment.objects.filter(element=subcomponent, assessment=assessment).\
                    order_by('date_created')
            else:
                comments = AssessmentComponentComment.objects.filter(element=component, assessment=assessment).\
                    order_by('date_created')

        # formset definition
        fs = modelformset_factory(AssessmentComponentQuestion, max_num=0, exclude=[],
                                             form=AssessmentComponentQuestionForm)

        if request.method == 'POST':
            f_set = fs(request.POST, request.FILES)

            if f_set and f_set.is_valid():

                not_applicable_responses_treatment(f_set)
                trace_updated_fields(f_set, person, assessment)
                # get assessment element to recalculate scoring
                a_element = None
                for f in f_set:
                    # get question
                    a_element = f.instance.assessment_element

                    print("assessment_element.element.name: " + f.instance.assessment_element.element.name)
                    print("component.name: " + f.instance.component.name)
                    sys.stdout.flush()

                    break
                f_set.save()

                # send signal to recalculate score of element
                recalculate_element_score.send(sender=a_element, element=a_element)

                # navigate to next component
                url_to_redirect = "/component/" + assessment_id + SLASH
                if third_component and third_component.next_one:
                    url_to_redirect += str(component.id) + SLASH
                    url_to_redirect += str(subcomponent.id) + SLASH
                    url_to_redirect += str(third_component.next_one.id) + SLASH
                else:
                    if subcomponent and subcomponent.next_one:
                        url_to_redirect += component.id + SLASH
                        url_to_redirect += subcomponent.next_one.id + SLASH
                    else:
                        if component.next_one:
                            url_to_redirect += component.next_one.id + SLASH


                return redirect(url_to_redirect, context_instance=RequestContext(request))
            else:
                # TODO: additional treatment of errors if needed
                print("fs_sf not informed or not valid!")
                print(str(f_set.errors))
                sys.stdout.flush()
        else:
            # formsets
            query_set = AssessmentComponentQuestion.objects.filter(component=third_component).order_by('order')
            f_set = fs(queryset=query_set)

        # return page
        template = loader.get_template(TEMPLATE_COMPONENTS_PAGE)
        context = RequestContext(request, {
            'fs': f_set,
            'person': person,
            'left_elements': left_elements,
            'menu_elements': menu_elements,
            'menu_horizontal_elem_width': menu_horizontal_elem_width,
            'page': "city_id",
            'assessment': assessment,
            'section': component,
            'subsection': subcomponent,
            'third_component': third_component,
            'comments': comments,
            'considerations': considerations,
            'is_component': 'True',
        })
        return HttpResponse(template.render(context))
    except:
        if debug_is_on():
            raise
        else:
            return render_to_response(TEMPLATE_ERROR, {"error_description": sys.exc_info(), "crpt_url": CRPT_URL},
                                      context_instance=RequestContext(request))


@ensure_csrf_cookie
@login_required
def add_section_comment(request):
    """
    View to add comment to a section

    :param request:
    :return:
    """
    try:
        person = get_person(request)

        if request.method == "POST":
            # get values from form
            assessment_id = request.POST['assessment_id']
            section_id = request.POST['section_id']
            comment = request.POST['textComments']

            # get section and assessment
            section = CityIDSection.objects.get(id=section_id)
            assessment = Assessment.objects.get(id=assessment_id)
            # create comment
            my_comment = AssessmentCityIDSectionComment()
            my_comment.assessment = assessment
            my_comment.element = section
            my_comment.comment = comment
            my_comment.person = person
            my_comment.save()

            # trace action
            trace_action(TRACE_COMMENT, person, "User added comment in section: " + section.name)

            # send mail
            try:
                send_mail = request.POST['send_mail']
                t = Thread(target=send_comments_email, args=(my_comment.comment, section, person))
                t.start()
                # send_comments_email(my_comment.comment, section, person)
            except:
                # checkbox not set
                pass

            # redirect to section page
            url_to_redirect = "/city_id/" + assessment_id + SLASH
            if section.parent:
                url_to_redirect += str(section.parent.id) + SLASH
            url_to_redirect += str(section.id) + SLASH

            return redirect(url_to_redirect, context_instance=RequestContext(request))
        else:
            raise Exception("GET call to add new section comment")
    except:
        if debug_is_on():
            raise
        else:
            return render_to_response(TEMPLATE_ERROR, {"error_description": sys.exc_info(), "crpt_url": CRPT_URL},
                                      context_instance=RequestContext(request))


@ensure_csrf_cookie
@login_required
def duplicate_question(request, assessment_id, component_id=None, subcomponent_id=None, third_component_id=None,
                       initial_question_id=None):
    """
    View to generate a new question for local gov. jurisdiction

    :param request:
    :param assessment_id:
    :param component_id:
    :param subcomponent_id:
    :param third_component_id:
    :param initial_question_id:
    :return:
    """
    try:
        # create new question
        new_question = duplicate_question_function(initial_question_id)
    except:
        print("Error creating new question: ")
        print(sys.exc_info())
        sys.stdout.flush()
    finally:
        # redirect
        url_to_redirect = "/component/" + assessment_id + SLASH + component_id + SLASH + subcomponent_id + SLASH + \
                          third_component_id
        return redirect(url_to_redirect, context_instance=RequestContext(request))