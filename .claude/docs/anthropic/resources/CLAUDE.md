# Anthropic Resources Documentation

This directory contains prompt templates, use case guides, and example patterns from Anthropic's documentation. The resources are organized by category to help you find relevant patterns for your work on LLMitM v2.

---

## Reference Documentation

Essential reference materials for Claude API usage, terminology, and model specifications.

- [Overview](./overview.md) - Model cards and learning resources index
- [Glossary](./glossary.md) - Key terms and concepts for working with Claude and language models
- [Overview - Guides to common use cases](./overview_guides_to_common_use_cases.md) - Production guides for building common use cases with Claude
- [System Prompts](./system_prompts.md) - Core system prompts used on Claude.ai

---

## Code & Development (HIGH RELEVANCE)

**When to use**: Reference these when building code analysis features, implementing bug detection, generating Python code, or optimizing performance. These patterns are directly applicable to LLMitM v2's structured output validation and code generation needs.

- [Code clarifier](./code_clarifier.md) - Simplify and explain complex code in plain language
- [Code consultant](./code_consultant.md) - Suggest improvements to optimize Python code performance
- [Python bug buster](./python_bug_buster.md) - Detect and fix bugs in Python code
- [Function fabricator](./function_fabricator.md) - Create Python functions based on detailed specifications
- [Efficiency estimator](./efficiency_estimator.md) - Calculate the time complexity of functions and algorithms
- [Git gud](./git_gud.md) - Generate appropriate Git commands based on user-described version control actions

---

## Data Processing & Extraction (HIGH RELEVANCE)

**When to use**: Reference these for patterns on extracting structured data from unstructured text, parsing responses, and converting between data formats. Highly relevant for fingerprinting, ActionGraph compilation, and HTTP traffic analysis.

- [Data organizer](./data_organizer.md) - Turn unstructured text into bespoke JSON tables
- [CSV converter](./csv_converter.md) - Convert data from various formats (JSON, XML, etc.) into properly formatted CSV
- [Email extractor](./email_extractor.md) - Extract email addresses from a document into a JSON-formatted list
- [Spreadsheet sorcerer](./spreadsheet_sorcerer.md) - Generate CSV spreadsheets with various types of data
- [SQL sorcerer](./sql_sorcerer.md) - Transform everyday language into SQL queries
- [Airport code analyst](./airport_code_analyst.md) - Find and extract airport codes from text
- [Direction decoder](./direction_decoder.md) - Transform natural language into step-by-step directions

---

## Content Moderation & Security (HIGH RELEVANCE)

**When to use**: Reference these for adversarial validation patterns, input sanitization, and security-aware prompt engineering. Directly applicable to the Attack Critic agent and safety guardrails.

- [Content moderation](./content_moderation.md) - Content moderation techniques and best practices
- [Master moderator](./master_moderator.md) - Evaluate user inputs for potential harmful or illegal content
- [PII purifier](./pii_purifier.md) - Automatically detect and remove personally identifiable information (PII) from text documents

---

## Document Analysis & Summarization (MODERATE RELEVANCE)

**When to use**: Reference these for extracting key information from large documents, providing citations, and summarizing complex text. Useful for analyzing HTTP traffic logs and compiling reconnaissance reports.

- [Cite your sources](./cite_your_sources.md) - Get answers to questions about a document's content with relevant citations
- [Corporate clairvoyant](./corporate_clairvoyant.md) - Extract insights, identify risks, and distill key information from long corporate documents
- [Legal summarization](./legal_summarization.md) - Leverage Claude's advanced natural language processing for legal document summarization
- [Meeting scribe](./meeting_scribe.md) - Distill meetings into concise summaries including discussion topics, key takeaways, and action items
- [Memo maestro](./memo_maestro.md) - Compose comprehensive company memos based on key points

---

## Enterprise & Business Use Cases (MODERATE RELEVANCE)

**When to use**: Reference these for conversational agent patterns, ticket routing logic, and classification tasks. Some patterns applicable to step result classification and failure diagnosis.

- [Customer support agent](./customer_support_agent.md) - Leverage Claude's advanced conversational capabilities for customer support
- [Ticket routing](./ticket_routing.md) - Harness Claude's advanced natural language understanding for ticket routing
- [Review classifier](./review_classifier.md) - Categorize feedback into pre-specified tags and categorizations
- [Grading guru](./grading_guru.md) - Compare and evaluate the quality of written texts based on user-defined criteria
- [Tweet tone detector](./tweet_tone_detector.md) - Detect the tone and sentiment behind tweets

---

## Development Tools & Scripting (MODERATE RELEVANCE)

**When to use**: Reference these when generating configuration files, scripts, or markup. Applicable to ActionGraph generation and step handler implementation.

- [Excel formula expert](./excel_formula_expert.md) - Create Excel formulas based on user-described calculations or data manipulations
- [Google apps scripter](./google_apps_scripter.md) - Generate Google Apps scripts to complete tasks based on user requirements
- [LaTeX legend](./latex_legend.md) - Write LaTeX documents, generating code for mathematical equations, tables, and more
- [Website wizard](./website_wizard.md) - Create one-page websites based on user specifications

---

## Text Editing & Writing

**When to use**: Reference these for text transformation patterns, tone adjustment, and grammar correction. Less directly applicable to LLMitM v2 but useful for report generation.

- [Adaptive editor](./adaptive_editor.md) - Rewrite text following user-given instructions, such as with a different tone
- [Prose polisher](./prose_polisher.md) - Refine and improve written content with advanced copyediting techniques and suggestions
- [Grammar genie](./grammar_genie.md) - Transform grammatically incorrect sentences into proper English
- [Second-grade simplifier](./second_grade_simplifier.md) - Make complex text easy for young learners to understand

---

## Creative & Language Play

**When to use**: Reference these for creative text generation, wordplay, and linguistic tasks. Low relevance to LLMitM v2 core functionality.

- [Alliteration alchemist](./alliteration_alchemist.md) - Generate alliterative phrases and sentences for any given subject
- [Babel's broadcasts](./babels_broadcasts.md) - Create compelling product announcement tweets in the world's 10 most spoken languages
- [Emoji encoder](./emoji_encoder.md) - Convert plain text into fun and expressive emoji messages
- [Idiom illuminator](./idiom_illuminator.md) - Explain the meaning and origin of common idioms and proverbs
- [Mood colorizer](./mood_colorizer.md) - Transform text descriptions of moods into corresponding HEX codes
- [Neologism creator](./neologism_creator.md) - Invent new words and provide their definitions based on user-provided concepts or ideas
- [Polyglot superpowers](./polyglot_superpowers.md) - Translate text from any language into any language
- [Portmanteau poet](./portmanteau_poet.md) - Blend two words together to create a new, meaningful portmanteau
- [Product naming pro](./product_naming_pro.md) - Create catchy product names from descriptions and keywords
- [Pun-dit](./pun_dit.md) - Generate clever puns and wordplay based on any given topic
- [Simile savant](./simile_savant.md) - Generate similes from basic descriptions
- [Tongue twister](./tongue_twister.md) - Create challenging tongue twisters

---

## Interactive & Conversational

**When to use**: Reference these for conversational agent patterns, interactive guidance, and multi-turn dialogue. Applicable to Actor/Critic loop design and repair diagnosis.

- [Career coach](./career_coach.md) - Engage in role-play conversations with an AI career coach
- [Dream interpreter](./dream_interpreter.md) - Offer interpretations and insights into the symbolism of the user's dreams
- [Ethical dilemma navigator](./ethical_dilemma_navigator.md) - Help the user think through complex ethical dilemmas and provide different perspectives
- [Hal the humorous helper](./hal_the_humorous_helper.md) - Chat with a knowledgeable AI that has a sarcastic side
- [Mindfulness mentor](./mindfulness_mentor.md) - Guide the user through mindfulness exercises and techniques for stress reduction
- [Motivational muse](./motivational_muse.md) - Provide personalized motivational messages and affirmations based on user input
- [Perspectives ponderer](./perspectives_ponderer.md) - Weigh the pros and cons of a user-provided topic
- [Philosophical musings](./philosophical_musings.md) - Engage in deep philosophical discussions and thought experiments
- [Socratic sage](./socratic_sage.md) - Engage in Socratic style conversation over a user-given topic

---

## Games & Entertainment

**When to use**: Reference these for game logic, interactive challenges, or scenario-based reasoning. Low relevance to LLMitM v2 core functionality.

- [Cosmic Keystrokes](./cosmic_keystrokes.md) - Generate an interactive speed typing game in a single HTML file
- [Riddle me this](./riddle_me_this.md) - Generate riddles and guide the user to the solutions
- [Sci-fi scenario simulator](./sci_fi_scenario_simulator.md) - Discuss with the user various science fiction scenarios and associated challenges
- [Storytelling sidekick](./storytelling_sidekick.md) - Collaboratively create engaging stories with the user, offering plot twists and character development
- [Time travel consultant](./time_travel_consultant.md) - Help the user navigate hypothetical time travel scenarios and their implications
- [Trivia generator](./trivia_generator.md) - Generate trivia questions on a wide range of topics and provide hints when needed
- [VR fitness innovator](./vr_fitness_innovator.md) - Brainstorm creative ideas for virtual reality fitness games

---

## Specialized Domain Knowledge

**When to use**: Reference these for domain-specific prompt engineering patterns. Less directly applicable unless LLMitM v2 expands into specialized testing domains.

- [Alien anthropologist](./alien_anthropologist.md) - Analyze human culture and customs from the perspective of an alien anthropologist
- [Brand builder](./brand_builder.md) - Craft a design brief for a holistic brand identity
- [Culinary creator](./culinary_creator.md) - Suggest recipe ideas based on the user's available ingredients and dietary preferences
- [Futuristic fashion advisor](./futuristic_fashion_advisor.md) - Suggest avant-garde fashion trends and styles for the user's specific preferences
- [Interview question crafter](./interview_question_crafter.md) - Generate questions for interviews
- [Lesson planner](./lesson_planner.md) - Craft in depth lesson plans on any subject
