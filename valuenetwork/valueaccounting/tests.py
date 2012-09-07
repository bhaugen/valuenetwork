import datetime
from decimal import *

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User

from valuenetwork.valueaccounting.models import *

class CompensationTest(TestCase):

    def setUp(self):

        self.unit = Unit(
            unit_type="value",
            abbrev="OB",
            name="Obols",
        )
        self.unit.save()

        self.a_type = AgentType(
            name="T",
        )
        self.a_type.save()

        self.agent_A = EconomicAgent(
            name="A",
            agent_type=self.a_type,
        )
        self.agent_A.save()

        self.agent_B = EconomicAgent(
            name="B",
            agent_type=self.a_type,
        )
        self.agent_B.save()

        self.r_type = EconomicResourceType(
            name="RT",
            unit=self.unit,
        )
        self.r_type.save()

        self.e_type = EventType(
            name="Transfer",
            resource_effect = "xfer",
            unit_type="value",
        )
        self.e_type.save()

        self.role = Role(
            name="Whatever",
            rate=Decimal("11.00"),
        )
        self.role.save()

        self.p_type = ProcessType(
            name="Do Something",
        )
        self.p_type.save()

        self.process = Process(
            name="Do Something Now",
            process_type=self.p_type,
            start_date = datetime.date.today(),
        )
        self.process.save()

        self.event1 = EconomicEvent(
            event_type=self.e_type,
            event_date = datetime.date.today(),
            from_agent=self.agent_A,
            from_agent_role=self.role,
            to_agent=self.agent_B,
            resource_type=self.r_type,
            process=self.process,
            quantity=Decimal("10.00"),
            unit_of_quantity=self.unit,
            value=Decimal("10.00"),
            unit_of_value=self.unit,
        )
        self.event1.save()

        self.event2 = EconomicEvent(
            event_type=self.e_type,
            event_date = datetime.date.today(),
            from_agent=self.agent_B,
            from_agent_role=self.role,
            to_agent=self.agent_A,
            resource_type=self.r_type,
            process=self.process,
            quantity=Decimal("10.00"),
            unit_of_quantity=self.unit,
            value=Decimal("10.00"),
            unit_of_value=self.unit,
        )
        self.event2.save()

        self.compensation= Compensation(
            initiating_event=self.event1,
            compensating_event=self.event2,
            compensation_date = datetime.date.today(),
            compensating_value=Decimal("10.00"),
        )
        self.compensation.save()

    def test_valid_compensation(self):
        compensations = self.event1.my_compensations()
        self.assertEqual(compensations.count(),1)
        self.assertEqual(self.event1.compensation(),Decimal('10.00'))
        self.assertEqual(self.event1.value_due(),Decimal('0.00'))
        self.assertEqual(self.event1.is_compensated(),True)

    def test_mismatched_agents1(self):

        agent_C = EconomicAgent(
            name="C",
            agent_type=self.a_type,
        )
        agent_C.save()

        event3 = EconomicEvent(
            event_type=self.e_type,
            event_date = datetime.date.today(),
            from_agent=self.agent_B,
            from_agent_role=self.role,
            to_agent=agent_C,
            resource_type=self.r_type,
            process=self.process,
            quantity=Decimal("10.00"),
            unit_of_quantity=self.unit,
            value=Decimal("10.00"),
            unit_of_value=self.unit,
        )
        event3.save()

        compensation= Compensation(
            initiating_event=self.event1,
            compensating_event=event3,
            compensation_date = datetime.date.today(),
            compensating_value=Decimal("10.00"),
        )
        try:
            compensation.full_clean()
        except ValidationError, e:
            #import pdb; pdb.set_trace()
            self.assertEqual(e.message_dict.values()[0][0], u'Initiating event from_agent must be the compensating event to_agent.')

    def test_mismatched_agents2(self):

        agent_C = EconomicAgent(
            name="C",
            agent_type=self.a_type,
        )
        agent_C.save()

        event3 = EconomicEvent(
            event_type=self.e_type,
            event_date = datetime.date.today(),
            from_agent=agent_C,
            from_agent_role=self.role,
            to_agent=self.agent_A,
            resource_type=self.r_type,
            process=self.process,
            quantity=Decimal("10.00"),
            unit_of_quantity=self.unit,
            value=Decimal("10.00"),
            unit_of_value=self.unit,
        )
        event3.save()

        compensation= Compensation(
            initiating_event=self.event1,
            compensating_event=event3,
            compensation_date = datetime.date.today(),
            compensating_value=Decimal("10.00"),
        )
        try:
            compensation.full_clean()
        except ValidationError, e:
            #import pdb; pdb.set_trace()
            self.assertEqual(e.message_dict.values()[0][0], u'Initiating event to_agent must be the compensating event from_agent.')

    def test_mismatched_value_units(self):

        unit = Unit(
            unit_type="quantity",
            abbrev="KG",
            name="Kilograms",
        )
        self.unit.save()

        event3 = EconomicEvent(
            event_type=self.e_type,
            event_date = datetime.date.today(),
            from_agent=self.agent_B,
            from_agent_role=self.role,
            to_agent=self.agent_A,
            resource_type=self.r_type,
            process=self.process,
            quantity=Decimal("10.00"),
            unit_of_quantity=unit,
            value=Decimal("10.00"),
            unit_of_value=unit,
        )
        event3.save()

        compensation= Compensation(
            initiating_event=self.event1,
            compensating_event=event3,
            compensation_date = datetime.date.today(),
            compensating_value=Decimal("10.00"),
        )
        try:
            compensation.full_clean()
        except ValidationError, e:
            #import pdb; pdb.set_trace()
            self.assertEqual(e.message_dict.values()[0][0], u'Initiating event and compensating event must have the same units of value.')



