"""
Mock retrieval matches for the agent when no database/vector search exists.
Optional mock Reddit-style demand evidence. enhance_idea does not use this; it uses live search for traction.
"""

from .schemas import RetrievalMatch

# Same flavour as backend mock_data: realistic demand signals the agent can ground ideas in
MOCK_MATCHES: list[RetrievalMatch] = [
    RetrievalMatch(
        id="mock_1",
        title="Client hasn't paid in 90 days — what do I do?",
        text="I've sent three invoices and two reminder emails. They keep saying the check is in the mail. At this point I've done $4k of work and I'm seriously considering small claims court. Has anyone actually had success with that? I delivered the project in November. Sent the invoice same day. It's now February and I've heard nothing but 'we're processing it' for the last 6 weeks.",
        source="reddit",
        metadata={"subreddit": "freelance"},
    ),
    RetrievalMatch(
        id="mock_2",
        title="I always forget to log my hours and then have to guess at the end of the week",
        text="Every single week I tell myself I'll track as I go. Then I get in the zone and forget. By Friday I'm trying to reconstruct 40 hours from memory and I know I'm underbilling. Lost probably $2k last year from this alone. There has to be a better way.",
        source="reddit",
        metadata={"subreddit": "freelance"},
    ),
    RetrievalMatch(
        id="mock_3",
        title="Scope creep is killing me — client keeps adding 'small' requests",
        text="We agreed on a landing page. Now it's a landing page plus blog integration plus email capture plus three rounds of revisions. I've done 2x the original scope and they're acting like I'm being difficult for asking for more money.",
        source="reddit",
        metadata={"subreddit": "entrepreneur"},
    ),
    RetrievalMatch(
        id="mock_4",
        title="Invoice software recommendations? Everything I've tried is either too expensive or a nightmare",
        text="I've tried FreshBooks, Wave, and a bunch of others. Either they want $30/month for features I don't need, or the UX is so bad I spend more time fighting the software than actually getting paid. What do solo freelancers actually use?",
        source="reddit",
        metadata={"subreddit": "freelance"},
    ),
    RetrievalMatch(
        id="mock_5",
        title="Net 60 payment terms are destroying my cash flow",
        text="Just finished a $8k project. Client has Net 60 terms. So I won't see that money until March. I have rent due in January. How do you all handle this? Do you just refuse to work with Net 60 clients?",
        source="reddit",
        metadata={"subreddit": "entrepreneur"},
    ),
    RetrievalMatch(
        id="mock_6",
        title="Manual timesheets are such a waste of time — there has to be a better way",
        text="I spend like 2 hours every week filling out timesheets for different clients. Each one has a different format. Some want Excel, some want their portal, some want a PDF. There has to be a tool that does this automatically.",
        source="reddit",
        metadata={"subreddit": "freelance"},
    ),
    RetrievalMatch(
        id="mock_7",
        title="Chasing payments feels like a second job",
        text="I spend more time sending 'friendly reminders' and following up than I do on some projects. One client I had to chase for 4 months. At what point do you just give up and write it off?",
        source="reddit",
        metadata={"subreddit": "freelance"},
    ),
    RetrievalMatch(
        id="mock_8",
        title="Client changed requirements 3 times mid-project, now wants a discount",
        text="We had a signed SOW. They asked for changes. I documented them and said it would add 20% to the scope. They said fine. Now at the end they're saying the final deliverable doesn't match expectations and want 15% off. I'm livid.",
        source="reddit",
        metadata={"subreddit": "entrepreneur"},
    ),
]


def get_mock_matches() -> list[RetrievalMatch]:
    """Return mock retrieval matches for use when the request has no matches (no DB yet)."""
    return list(MOCK_MATCHES)
