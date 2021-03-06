import os
import sys

from threading import Thread

from django.conf import settings

project_path = "/Users/miquel/UN/0003-CRPTDEV/CRPT201511_BRW/"
sys.path.append(project_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'crpt201511.settings'

# OBS: to initialize Django in 1.7 and run python scripts. Do not include 'setup' in installed_apps
import django
django.setup()

from crpt201511.trace import trace_action
from crpt201511.models import *
from crpt201511.constants import *
from crpt201511.utils.assessment_utils import get_remote_folder_name
from crpt201511.utils.component_question_utils import *
from crpt201511.utils.hazard_utils import *


def test_threading():
    print("test_threading. Start.")
    person = Person.objects.get(first_name="Test")
    t = Thread(target=trace_action, args=(TRACE_LOGIN, person, person.name + " - " + person.role.name))
    t.start()
    print("test_threading. End.")


def test_version_selected():
    print("test_version_selected. Start.")
    version = AssessmentVersion.objects.order_by('-date_released')[0]
    print("Version: " + version.version)
    print("test_version_selected. End.")


def test_create_new_assessment_city_id(assessment):
    print("create_new_asessment_city_id. Start.")

    # create assessment elements - first parents
    for elem in Element.objects.filter(version=assessment.version, parent=None).order_by('id'):
        a_element = AssessmentElement()
        a_element.element = elem
        a_element.assessment = assessment
        a_element.save()
    # create assessment elements - then the rest
    for elem in Element.objects.filter(version=assessment.version).exclude(parent=None).order_by('id'):
        a_element = AssessmentElement()
        a_element.element = elem
        a_element.assessment = assessment
        print("element.name: " + elem.name)
        if elem.parent:
            print("element.parent.name: " + elem.parent.name)
            sys.stdout.flush()

            a_element.parent = AssessmentElement.objects.get(element=elem.parent, assessment=assessment)
        a_element.save()



    # new City ID. For each section create AssessmentCityIDStatements and correspondent responses
    cid_sections = CityIDSection.objects.all()
    for section in cid_sections:
        print("CtyID Section Start: " + str(section.name))
        # CharField
        cid_questions = CityIDQuestion.objects.filter(section=section).exclude(id__in=AssessmentCityIDQuestion.objects.all())
        for cid_question in cid_questions:
            a_cid_question = AssessmentCityIDQuestion()
            a_cid_question.question_short = cid_question.question_short
            a_cid_question.question_long = cid_question.question_long
            a_cid_question.order = cid_question.order
            a_cid_question.help_text = cid_question.help_text
            a_cid_question.placeholder = cid_question.placeholder
            a_cid_question.not_applicable = cid_question.not_applicable
            a_cid_question.version = cid_question.version
            a_cid_question.section = section
            a_cid_question.assessment = assessment
            a_cid_question.choices = cid_question.choices
            a_cid_question.multi = cid_question.multi
            a_cid_question.question_type = cid_question.question_type
            if cid_question.element:
                print("Get Assessment Element for element: " + cid_question.element.name)
                a_cid_question.assessment_element = AssessmentElement.objects.filter(element=cid_question.element)[0]
            a_cid_question.save()
            # creation of other tx choices for this assessment
            if cid_question.choices.strip() == OTHER_TX:
                for other_tx in ChoicesOtherTx.objects.all():
                    a_cid_other_tx = AssessmentCityIDChoicesOtherTx()
                    a_cid_other_tx.name = other_tx
                    a_cid_other_tx.assessment = assessment
                    a_cid_other_tx.save()
            a_cid_question.save()

        print("CityID Section End: " + str(section.name))
    print("create_new_asessment_city_id. End.")


def test_create_new_assessment_components(assessment):
    print("test_create_new_assessment_components. Start.")

    # Components (indicators). For each component create AssessmentQuestions and correspondent responses
    components = Component.objects.all()
    for component in components:
        print("Component Start: " + component.name)
        # CharField
        component_questions = ComponentQuestion.objects.filter(component=component).\
            exclude(id__in=AssessmentComponentQuestion.objects.all())
        for question in component_questions:
            a_question = AssessmentComponentQuestion()
            a_question.question_short = question.question_short
            a_question.question_long = question.question_long
            a_question.order = question.order
            a_question.help_text = question.help_text
            a_question.placeholder = question.placeholder
            a_question.not_applicable = question.not_applicable
            a_question.version = question.version
            a_question.component = component
            a_question.assessment = assessment
            a_question.element = question.element
            a_question.has_mov = question.has_mov
            a_question.units = question.units
            # dimension
            a_question.dimension = question.dimension
            # scorable consideration
            if question.units == 1 or question.choices == MOV_SOURCE or \
                            question.choices == SC1 or question.choices == SC2 or question.choices == SC3 or \
                            question.choices == SC4 or question.choices == SC5:
                a_question.scorable = True
            a_question.mov_position = question.mov_position
            a_question.add_type = question.add_type
            a_question.mov_type = question.mov_type
            a_question.question_type = question.question_type
            a_question.choices = question.choices
            # set max num of choices
            if a_question.choices != "":
                set_max_num_of_choices(a_question)
            a_question.multi = question.multi
            # look for assessment element
            if question.element:
                print("Get Assessment Element for element: " + question.element.name)
                a_question.assessment_element = AssessmentElement.objects.get(element=question.element,
                                                                              assessment=assessment)

            # save question
            a_question.save()

            # treatment of choices
            if str(question.choices).strip() == MC1:
                if len(AssessmentChoicesMC1.objects.all()) == 0:
                    for elem in ChoicesMC1.objects.all():
                        a_cid_other_tx = AssessmentChoicesMC1()
                        a_cid_other_tx.name = elem.name
                        a_cid_other_tx.assessment = assessment
                        a_cid_other_tx.save()
            # treatment of choices
            if str(question.choices).strip() == MC3:
                if len(AssessmentChoicesMC3.objects.all()) == 0:
                    for elem in ChoicesMC3.objects.all():
                        a_cid_other_tx = AssessmentChoicesMC3()
                        a_cid_other_tx.name = elem.name
                        a_cid_other_tx.assessment = assessment
                        a_cid_other_tx.save()
            # treatment of choices
            if str(question.choices).strip() == MC4:
                if len(AssessmentChoicesMC4.objects.all()) == 0:
                    for elem in ChoicesMC4.objects.all():
                        a_cid_other_tx = AssessmentChoicesMC4()
                        a_cid_other_tx.name = elem.name
                        a_cid_other_tx.assessment = assessment
                        a_cid_other_tx.save()

        print("Component End: " + component.name)

    print("test_create_new_assessment_components. End.")


def test_get_remote_folder_name():
    print("test_get_remote_folder_name.Start")

    assessment = Assessment.objects.all()[:1].get()
    section = CityIDSection.objects.all()[:1].get()

    print("remote folder name: " + get_remote_folder_name(assessment, section))


    print("test_get_remote_folder_name.End")


def test_create_new_assessment_hazards(assessment):
    print("test_create_new_assessment_hazards.Start")

    # create hazard types
    for ht in HazardType.objects.all().order_by('id'):
        aht = AssessmentHazardType()
        aht.assessment = assessment
        aht.hazard_type = ht
        aht.save()
        # create hazard subtypes
        for hst in HazardSubtype.objects.filter(hazard_type=ht):
            ahst = AssessmentHazardSubtype()
            ahst.h_subtype = hst
            ahst.assessment = assessment
            ahst.a_h_type = aht
            ahst.save()



    """
    # create hazard subtypes
    for hst in HazardSubtype.objects.all().order_by('id'):
        ahst = AssessmentHazardSubtype()
        ahst.h_subtype = hst
        ahst.assessment = assessment
        ahst.a_h_type = AssessmentHazardType.objects.get(assessment=assessment, hazard_type=hst.hazard_type)
        ahst.save()
    """

    # create hazard causes and consequences
    for ht in HazardType.objects.all().order_by('id'):
        for a_h_t in AssessmentHazardType.objects.filter(assessment=assessment).order_by('id'):
            cause = AssessmentHazardCause()
            cause.assessment = assessment
            cause.a_h_type = AssessmentHazardType.objects.get(hazard_type=ht, assessment=assessment)
            cause.a_h_type_cause = a_h_t
            cause.save()
            conseq = AssessmentHazardConsequence()
            conseq.assessment = assessment
            conseq.a_h_type = AssessmentHazardType.objects.get(hazard_type=ht, assessment=assessment)
            conseq.a_h_type_consequence = a_h_t
            conseq.save()
    # create hazard impacts
    for ht in AssessmentHazardType.objects.filter(assessment=assessment).order_by('id'):
        for ei in ElementImpact.objects.all().order_by('id'):
            aei = AssessmentElementImpact()
            aei.elem_impact = ei
            aei.assessment = assessment
            aei.a_h_type = ht
            aei.save()
    print("test_create_new_assessment_hazards.End")


def test_create_new_assessment_stakeholders(assessment):
    print("test_create_new_assessment_stakeholders.Start")

    # create assessment stakeholders
    for s in Stakeholder.objects.all().order_by('id'):
        a_s = AssessmentStakeholder()
        a_s.stakeholder = s
        a_s.assessment = assessment
        a_s.save()

    print("test_create_new_assessment_stakeholders.End")

def test_obtain_max_selected_value():
    print("test_obtain_max_selected_value.Start")
    question = AssessmentComponentQuestion.objects.get(id=54)
    print("QUESTION: " + question.question_short)
    print("Response: " + str(question.response))
    resp_length = len(str(question.response))
    try:
        max_selected_value = int(str(question.response)[resp_length-3:resp_length-2])
    except:
        max_selected_value = 0
    print("Max selected value: " + str(max_selected_value))
    print("test_obtain_max_selected_value.End")


def test_create_new_assessment_for_city(city_name):
    print("test_create_new_assessment_for_city. Start. city_name: " + str(city_name))
    assessment = Assessment()
    city = City.objects.get(name=city_name)
    assessment.name = city_name + " - assessment"
    assessment.city = city
    assessment.considerations = "Test Assessment"
    assessment.focal_point_started = Person.objects.filter(city=city)[0]
    assessment.version = AssessmentVersion.objects.order_by('-date_released')[0]
    assessment.save()
    print("test_create_new_assessment_for_city. End. city_id: " + str(city_name))
    return assessment


def test_ammend_a_h_t_causes_conseqs():
    print("test_ammend_a_h_t_causes_conseqs. Start.")
    for city in City.objects.all():
        print("Ammend. City: " + str(city.name) + " Start")
        # get assessment
        try:
            assessment = Assessment.objects.get(city_id=city.id)
            # create new assessment hazards
            test_create_new_assessment_hazards(assessment)
        except:
            assessment = None
        print("Ammend. City: " + str(city.name) + " End")


    print("test_ammend_a_h_t_causes_conseqs. End.")


def test_get_list_of_ids():
    print("test_get_list_of_ids.Start")
    response = "[u'0',u'1',u'2']"
    lista = get_list_of_ids(response)
    print("List of ids: " + str(lista))
    print("test_get_list_of_ids.End")


def test_simple():
    print("value: " + str(int("YES" == YES_STR)))
    print("value: " + str(int("" == YES_STR)))


def test_hazards_selected():
    assessment = Assessment.objects.all()[:1].get()
    return get_hazards_selected(assessment)


def test_create_assessment_city(city_name):
    print("test_create_assessment_city. Start. City:" + city_name)
    assessment = test_create_new_assessment_for_city(city_name)
    test_create_new_assessment_city_id(assessment)
    test_create_new_assessment_components(assessment)
    test_create_new_assessment_hazards(assessment)
    test_create_new_assessment_stakeholders(assessment)

    print("test_create_assessment_city. End. City:" + city_name)


def test_findall():
    list = get_list_of_ids("[u'457', u'458']")
    print(str(list[0]))


def test_ammend_a_city_id_other_tx():
    print("test_test_ammend_a_city_id_other_tx. Start.")
    for a_c_id_q in AssessmentCityIDQuestion.objects.filter(choices="OTHER_TX").order_by('id'):
        for choice_other_tx in ChoicesOtherTx.objects.all():
            a_choice_other_tx = AssessmentCityIDChoicesOtherTx()
            a_choice_other_tx.assessment = a_c_id_q.assessment
            a_choice_other_tx.name = choice_other_tx.name
            a_choice_other_tx.save()
    print("test_test_ammend_a_city_id_other_tx. End.")



if __name__ == "__main__":

    #test_threading()
    #test_version_selected()
    #test_get_remote_folder_name()
    #test_multi()
    #test_obtain_max_selected_value()
    #test_get_list_of_ids()
    #test_hazards_selected()
    #test_findall()
    """
    test_create_assessment_city("Test")
    test_create_assessment_city("Barcelona")
    test_create_assessment_city("Ensenada")
    test_create_assessment_city("La Paz")
    test_create_assessment_city("Carmen")
    test_create_assessment_city("Tapachula de Cordoba")
    test_create_assessment_city("Ciudad Juarez")
    test_create_assessment_city("Saltillo")
    test_create_assessment_city("Manzanillo")
    test_create_assessment_city("Victoria de Durango")
    test_create_assessment_city("Leon de los Aldama")
    test_create_assessment_city("Acapulco")
    test_create_assessment_city("Puerto Vallarta")
    test_create_assessment_city("Tepic")
    test_create_assessment_city("Monterrey")
    test_create_assessment_city("Oaxaca")
    test_create_assessment_city("Atlixco")
    test_create_assessment_city("Playa del Carmen")
    test_create_assessment_city("Mazatlan")
    test_create_assessment_city("Tampico")
    """

    #test_ammend_a_h_t_causes_conseqs()
    test_ammend_a_city_id_other_tx()
