from .domain import Case,Fact,Event,Reminder
from datetime import date,timedelta

def demo_case():
    c=Case(title='Headphones refund',location='Bengaluru, Karnataka',goal='Refund of ₹3,499 to the original payment method',story='SYNTHETIC DEMO: I bought headphones from Example Electronics for ₹3,499. They were faulty. I returned them and have not received a refund. I want to understand the next step.',prior_proceedings='No')
    e=c.add_evidence('Demo merchant message.txt','Example Electronics\nOrder: DEMO-2048\nAmount paid: INR 3499\nReturn pickup completed: 12 October 2026\nYour return will be inspected within seven working days.','Merchant correspondence')
    c.facts=[Fact(label='Merchant',value='Example Electronics',confirmed=True),Fact(label='Amount paid',value='₹3,499',status='Source-supported',source_id=e.id,quote='Amount paid: INR 3499',confirmed=True),Fact(label='Pickup date',value='12 October 2026',status='Source-supported',source_id=e.id,quote='Return pickup completed: 12 October 2026',confirmed=True),Fact(label='Refund approval',value='Not established; the message mentions inspection only.',status='Unknown')]
    c.events=[Event(date='2026-10-12',description='Return pickup completed',source=e.id)]
    c.reminders=[Reminder(title='Check merchant response',date=(date.today()+timedelta(days=3)).isoformat(),kind='Suggested follow-up',basis='Convenience reminder, not a legal deadline')]
    return c
