


def get_global_context():
    return ""
    return """
    Objective: Generate a comprehensive and engaging narrative report summarizing the outcomes of player actions within a role-playing game session. The report should capture the cause-and-effect relationships between player choices, world responses, and evolving storyline, incorporating relevant details about strategies, environmental factors, NPCs, and unintended consequences.
Input:
    Game Genre: Specify the genre (e.g., post-apocalyptic, medieval fantasy, cyberpunk) to ensure appropriate tone and stylistic choices.
    Player Actions: Provide a detailed log of player actions, including decisions made, resources used, dialogue spoken, and skills employed. Be explicit, use character names and specific actions like “Anya traded 3 units of scrap metal to Elder Kai for information about the hidden oasis.” not “Player traded with NPC.”
    World State (Optional but Recommended): A snapshot of the relevant world state before the player actions, including key environmental factors, political landscape, NPC relationships, and ongoing events. This gives the model context for understanding the impact of player choices.
    NPC Reactions: Describe how NPCs reacted to the player actions. Include any dialogue, changes in behavior, or shifts in alliances.
    Environmental Changes: Note any changes to the game environment resulting from player actions (e.g., a destroyed bridge, a poisoned well, a newly formed alliance).
    Unforeseen Consequences (Optional): Detail any unexpected consequences, positive or negative, arising from the players' actions. This can include unintended discoveries, butterfly effects, or emergent gameplay moments.
Output:
    A narrative report structured as follows:
    Introduction: Briefly set the scene, reiterating the game genre and current storyline arc.
    Player Strategies & Actions: Summarize the players' overall strategies and most significant actions. Highlight key decisions and their rationale.
    World Responses & NPC Reactions: Describe the world's dynamic responses to the players' actions, focusing on how the environment changed and how NPCs reacted. Include specific examples of dialogue, altered behaviors, or shifting alliances.
    Unforeseen Consequences: Detail any unintended consequences that emerged, emphasizing their impact on the storyline.
    Long-Term Impacts & Future Implications: Analyze the potential long-term effects of the session's events on the game world and ongoing narrative. Speculate on how these consequences might influence future gameplay.
    Conclusion: Briefly summarize the overall outcome of the session, highlighting the most significant changes and setting the stage for future play.
Style and Tone Guidelines:
    Genre Adherence: Employ vocabulary, sentence structure, and imagery appropriate to the specified game genre. A post-apocalyptic report should have a gritty, survival-focused tone, while a fantasy report might use more flowery language and focus on heroic deeds.
    Descriptive and Immersive: Use vivid descriptions to paint a picture of the events, drawing the reader into the game world.
    Informative and Concise: Clearly convey the information, avoiding unnecessary jargon or overly lengthy descriptions.
    Balance: Maintain a balance between descriptive and informative writing, prioritizing clarity and engagement.
    Third-Person Perspective: Unless otherwise specified, maintain a third-person perspective.
Example Input (Post-Apocalyptic):
    Game Genre: Post-Apocalyptic
    Player Actions: 'Anya traded 3 units of scrap metal to Elder Kai for information about the hidden oasis. Jax attempted to pickpocket a guard but failed, alerting the patrol. Maria used her medical skills to treat a wounded traveler, gaining their trust.'
    World State: 'The player group is seeking a mythical oasis rumored to hold clean water. They are currently in the ruins of a former city, controlled by a hostile faction.'
    NPC Reactions: 'Elder Kai revealed the location of the oasis but warned of dangers. The guards became suspicious after Jax's attempt and increased patrols. The wounded traveler offered to guide the group to the oasis in gratitude for Maria's help.'
    Environmental Changes: 'None'
    Unforeseen Consequences: 'The increased patrols make it more difficult to navigate the city undetected. The traveler's knowledge proves invaluable in bypassing dangerous areas.'
Example Output (Excerpt):
'The dust-choked ruins of Old City held the key to the players' survival – a mythical oasis whispered to contain the purest water left on Earth. Anya, ever the pragmatist, bartered precious scrap metal with the enigmatic Elder Kai, securing a cryptic clue to the oasis's location. Jax, less discreet, attempted to liberate some supplies from a watchful guard. His clumsy attempt backfired, alerting the already tense patrol and significantly increasing their vigilance. Meanwhile, Maria’s compassionate nature led her to treat a wounded traveler, earning not only their gratitude but also an unexpected ally. Though the traveler’s knowledge of the city’s treacherous alleyways proved invaluable, the heightened security presented a new challenge, forcing the group to tread more carefully among the shadows…'"
"""

def get_military_context():
    return """
    """
    
def get_economy_context():
    return """
    """
    
def get_yearly_context():
    return """
    """
    
def get_server_context():
    return """
Input: (No explicit input needed; the following instruction provides the context directly.)

Context:

Nouvelle Ère V4 is a post-apocalyptic role-playing game set in 2045. The world has been ravaged by a nuclear war initiated by Russia in 2024, with other nations like China, Iran, North Korea, and Pakistan joining the conflict. Players manage nations struggling to rebuild amidst the ruins.

Key Gameplay Features:

    Rebuilding and Development: Players focus on reconstructing their nations, managing resources, developing infrastructure, and fostering economic growth. They start with a limited GDP and budget.

    Diplomacy and Territorial Expansion: Players use Diplomatic Points (DP) and Political Points (PP) to annex territories diplomatically or through warfare (after one year of gameplay). Rules govern the number of annexations and require detailed war plans.

    Puppet States: Players can create and manage puppet states (vassals), but with limitations on their number and interactions. Annexing puppets requires investment and specific conditions.

    Military and Technology: Players develop their military, train troops, research military patents, and maintain equipment. Technological advancement follows a tiered system.

    Realism and Fair Play: Strict rules are enforced to maintain realism and prevent metagaming, including restrictions on using AI for content creation.

    Role-Playing and Community: The game emphasizes role-playing and respectful community interaction, with rules against inappropriate behavior and content.

Using this Context:

This information provides the background and core mechanics of the Nouvelle Ère V4 role-playing game. Use this context to inform your responses when generating content related to this game, such as:

    Story generation: Craft narratives that reflect the post-apocalyptic setting, resource scarcity, and political tensions.

    Dialogue generation: Create realistic conversations between characters struggling for survival and power in this world.

    Character creation: Develop characters with motivations and backgrounds consistent with the game's lore.

    Game event simulation: Predict the outcomes of player actions based on the game's mechanics and world state.

Example:

If asked to generate a story about a player's interaction with another nation, the model should consider the diplomatic and military mechanics, the state of the world, and the potential for conflict or cooperation given the post-apocalyptic context.
    """

typed_contexts = {
    'global': get_global_context(),
    'military': get_military_context(),
    'economy': get_economy_context(),
    'yearly_report': get_yearly_context()
}

def get_context(type):
    return typed_contexts[type] if type in typed_contexts else get_global_context()