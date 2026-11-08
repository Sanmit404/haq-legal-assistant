"""Curated navigation guidance. No automated entitlement or deadline determinations."""
SOURCES = {
 'nch': {'title':'National Consumer Helpline', 'url':'https://consumerhelpline.gov.in/public/about',
         'checked':'2026-11-08', 'scope':'Consumer grievances, India',
         'excerpt':'NCH is a Pre-Litigation stage step.',
         'guidance':'NCH provides a pre-litigation grievance channel. A closure is not proof of refund or satisfactory resolution. Do not promise a resolution time.'},
 'ejagriti': {'title':'e-Jagriti filing help', 'url':'https://e-jagriti.gov.in/help-docs',
         'checked':'2026-11-08', 'scope':'Consumer commission filing guidance',
         'excerpt':'Consumer Complaint (CC) Case Filing',
         'guidance':'Check the current official filing instructions for document applicability, jurisdiction, fees, signatures and declarations. Drafts are not filed or notarised by Haq.'},
 'rbi': {'title':'RBI Integrated Ombudsman FAQ', 'url':'https://m.rbi.org.in/commonman/english/scripts/FAQs.aspx?Id=3407',
         'checked':'2026-11-08', 'scope':'Covered regulated entities; scheme and dates require review',
         'excerpt':'RB-IOS, 2026 replaces the Reserve Bank - Integrated Ombudsman Scheme, 2021.',
         'guidance':'Verify the applicable scheme version, entity coverage, prior complaint proof, prerequisites and overlapping proceedings. Older complaints have transition rules. Do not calculate deadlines or decide maintainability from this summary.'},
 'telelaw': {'title':'Tele-Law: access to legal advice', 'url':'https://www.tele-law.in/faq.html',
         'checked':'2026-11-08', 'scope':'Professional advice access',
         'excerpt':'The service is free of cost for all citizens.',
         'guidance':'Direct users to the official service for access instructions. Do not claim a booking, lawyer assignment or availability.'},
 'nalsa': {'title':'NALSA legal aid', 'url':'https://nalsa.gov.in/faqs/',
         'checked':'2026-11-08', 'scope':'Eligibility-based legal assistance',
         'excerpt':'One can directly contact on NALSA Helpline Toll-Free Number 15100 to seek urgent legal assistance.',
         'guidance':'Legal aid is subject to the official eligibility framework. The authority makes the decision; do not approve or reject eligibility.'},
 'cyber': {'title':'National Cybercrime Reporting Portal', 'url':'https://cybercrime.gov.in/',
         'checked':'2026-11-08', 'scope':'Suspected cybercrime / financial fraud',
         'excerpt':'', 'guidance':'Suspected financial cyber fraud requires prompt official reporting through 1930 and the official cybercrime portal; contact the bank through verified channels. Do not wait for an ordinary grievance workflow.'},
}


def route_cards(category, prior):
    if category == 'Consumer purchase':
        cards = [('Contact the merchant', 'Prepare a factual complaint and record the response. Verify the recipient using your receipt or the official merchant website.', None),
                 ('Explore NCH', 'Prepare your grievance and evidence. Check the official portal for applicability and instructions.', 'nch'),
                 ('Prepare for a consumer filing', 'Use the current filing guide; jurisdiction, document requirements and deadlines need review.', 'ejagriti')]
    elif category == 'Banking / payment':
        cards = [('Contact the bank or payment provider', 'Record the original complaint and acknowledgement. Use verified official contact details.', None),
                 ('Check RBI coverage and prerequisites', 'Entity coverage, prior response, applicable scheme and existing proceedings must be checked before escalation.', 'rbi')]
    else:
        cards = [('Prepare a professional handoff', 'Rental and employment rules depend on location and circumstances. Organise facts and seek individual advice.', 'telelaw')]
    if prior != 'No':
        cards.insert(0, ('Review existing proceedings first', 'You indicated existing proceedings or uncertainty. Get professional advice before starting an overlapping process.', 'telelaw'))
    return cards
