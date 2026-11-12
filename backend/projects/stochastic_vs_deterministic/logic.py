"""Ground-truth answers and the comparison logic for the temperature demo."""
from sentence_transformers import SentenceTransformer, util

from shared.llm import client, ANTHROPIC_MODEL

model = SentenceTransformer("all-MiniLM-L6-v2")

GROUND_TRUTHS = {
    "What is Meeting Digest?": (
        "Meeting Digests is a feature within Salesforce Meetings that enhances sales reps' "
        "interactions with prospects and customers by providing a unified view of meeting information. "
        "It helps sales reps prepare for meetings by gathering and sharing insights about attendees, "
        "meeting details, and related activities on a single page."
    ),

    "How can I use Meeting Digest?": (
        "To start using Meeting Digest, here are some steps:\n"
        "1. Enable Salesforce Meetings: Ensure that Meeting Digest is enabled.\n"
        "2. Assign Permissions: Reassign users to the permission set.\n"
        "3. Utilize Einstein Activity Capture: Implement an activity sync.\n"
        "4. Prepare for Meetings: Use the Meeting Digest to gather and share information before meetings.\n"
        "5. Take Action on Attendee Details: Update attendee details, start emails, or add new records."
    ),

    "How can Meeting Digest drive value?": (
        "Here are some ways it can add value:\n\n"
        "1. Unified Information: Meeting Digest unifies all relevant information about meeting attendees.\n"
        "2. Enhanced Engagement: The Meeting Studio feature within Meeting Digest allows reps to keep attendees engaged during virtual meetings.\n"
        "3. Actionable Insights: Meeting Digest provides insights into high-priority cases and outstanding customer requests.\n"
        "4. Streamlined Follow-Up: After the meeting, Meeting Digest offers reminders and quick actions for follow-up tasks.\n"
        "5. Improved Collaboration: With the ability to update attendee details directly from the Meeting Digest, sales reps can stay focused on meeting preparation and execution."
    )
}
