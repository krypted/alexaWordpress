import feedparser
import re


def lambda_handler(event, context):
	print("event.session.application.applicationId=" +
		  event['session']['application']['applicationId'])
	

	if event['session']['new']:
		on_session_started({'requestId': event['request']['requestId']},
						   event['session'])

	if event['request']['type'] == "LaunchRequest":
		return on_launch(event['request'], event['session'])
	elif event['request']['type'] == "IntentRequest":
		return on_intent(event['request'], event['session'])
	elif event['request']['type'] == "SessionEndedRequest":
		return on_session_ended(event['request'], event['session'])
 
 
def on_session_started(session_started_request, session):
	print("on_session_started requestId=" + session_started_request['requestId']
		  + ", sessionId=" + session['sessionId'])
 
 
def on_launch(launch_request, session):
	print("on_launch requestId=" + launch_request['requestId'] +
		  ", sessionId=" + session['sessionId'])

	return get_welcome_response()
 
 
def on_intent(intent_request, session):
	print("on_intent requestId=" + intent_request['requestId'] +
		  ", sessionId=" + session['sessionId'])
 
	intent = intent_request['intent']
	intent_name = intent_request['intent']['name']
 
	try:
		session['attributes']
	except KeyError:
		session['attributes'] = {}

	global route
	try:
		session['attributes']['route']
	except KeyError:
		route = None
	else:
		route = session['attributes']['route']

	if route == None:
		if intent_name == "getRecentPostIntent":
			route = "83205"

	if not route == None:
		if route == "83205":
			return getrecentpostintent_action(intent, session)

	else:
		if intent_name == "AMAZON.StopIntent":
			return handle_session_end_request()
		elif intent_name == "getrecentpostintent":
			return getrecentpostintent_action(intent, session)
		else:
			raise ValueError("invalid intent")

 
 
def on_session_ended(session_ended_request, session):
	print("on_session_ended requestId=" + session_ended_request['requestId'] +
		  ", sessionId=" + session['sessionId'])

 
# --------------- Functions that control the skill's behavior ------------------
 
 
def get_welcome_response():
	session_attributes = {}
	card_title = "Welcome"
	speech_output = "Welcome to the krypted dot com Alexa Skill, To get the most recent post, say \"Get the most recent post\""

	reprompt_text = "What can I help you with?"
	should_end_session = False
	return build_response(session_attributes, build_speechlet_response(speech_output, reprompt_text, should_end_session, card_title=card_title))

def handle_session_end_request():
	card_title = None
	speech_output = None
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(
		"", "", should_end_session))

def getrecentpostintent_action(intent, session):
	global route

	if route == "83205":
		feed = feedparser.parse('http://krypted.com/feed/')
		print(feed.entries[-1].content)
		post = cleanhtml(feed.entries[0].content[0]['value']).replace("-", " dash ")
		
		print(post)
		speech_output = "Here's the most recent post: " + post
		reprompt_text = ""
		shouldEndSession = False
		session_attributes = {}

		return build_response(session_attributes, build_speechlet_response(speech_output, reprompt_text, shouldEndSession))





# --------------- Helper Functions --------------- #

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

# --------------- Helpers that build all of the responses ----------------------
 
def build_show_response(options):
	templateType = options['template']
	title = options['title']

	directives = {
		"directives": [
            {
                "type": "Display.RenderTemplate",
                "template": {
                    "type": templateType,
                    
                    "title": "BodyTemplate2 Display Title",
                    "token": "TOKEN",
                    "backButton": "HIDDEN"
                }
            }
        ]
	}

	if "backgroundImage" in options:
		backgroundImage = options['backgroundImage']
		backgroundImageURL = backgroundImage["url"]

		if "contentDescription" in backgroundImage:
			bgContentDesc = backgroundImage["contentDescription"]
			directive = {
				"backgroundImage": {
					"contentDescription": bgContentDesc,
					"sources": [
						{
							"url": backgroundImageURL
						}
					]
				}
			}
		else:
			directive = {
				"backgroundImage": {
					"sources": [
						{
							"url": backgroundImageURL
						}
					]
				}
			}
		directives['directives'][0]['template'].update(directive)

	if "image" in options:
		image = options['image']
		imageURL = image["url"]
		if "contentDescription" in image:
			imgContentDesc = image["contentDescription"]

			directive = {
				"image": {
					"contentDescription": imgContentDesc,
					"sources": [
						{
							"url": imageURL
						}
					]
				}
			}
		else:
			imgContentDesc = ""

			directive = {
				"image": {
					"sources": [
						{
							"url": imageURL
						}
					]
				}
			}


			directives['directives'][0]['template'].update(directive)

	if "textContent" in options:
		textContent = options['textContent']
		texts = {}
		primaryText = textContent['primaryText']
		texts.update({"primaryText": {"text": primaryText, "type": "PlainText"}})

		try:
			secondaryText = textContent['secondaryText']
			texts.update({"secondaryText": {"text": secondaryText, "type": "PlainText"}})
		except KeyError:
			secondaryText = None

		try:
			tertiaryText = textContent['tertiaryText']
			texts.update({"tertiaryText": {"text": tertiaryText, "type": "PlainText"}})
		except KeyError:
			tertiaryText = None

		directives['directives'][0]['template'].update({"textContent": texts})

	print(directives)
	return directives


def build_speechlet_response(response, reprompt, shouldEndSession, card_title=None, card_text=None, directive=None):
	base_response = {
		'outputSpeech': {
			'type': 'PlainText',
			'text': response
		},
		'reprompt': {
			'outputSpeech': {
				'type': 'PlainText',
				'text': reprompt
			}
		},
		'shouldEndSession': shouldEndSession
	}

	
	if not card_title == None:
		if card_text == None:
			card_text = response

		base_response.update({
			"card": {
				"type": "Standard",
				"title": card_title,
				"text": card_text
			}
		})

	if not directive == None:
		if type(directive) is dict:
			directiveResponse = build_show_response(directive)
		else:
			raise TypeError("build_show_response expected dict of options")

		base_response.update(directiveResponse)

	return base_response
 
 
def build_response(session_attributes, speechlet_response):
	return {
		'version': '1.0',
		'sessionAttributes': session_attributes,
		'response': speechlet_response
	}

def readList(listToRead):
	choice_number = 1
	speech_output = ""
	for item in listToRead:
		if item == listToRead[-1]:
			end_period = True
			speech_output += "or "
		else:
			end_period = False

		speech_output += str(choice_number) + " for " + str(item)

		if end_period == True:
			speech_output += "."
		else:
			speech_output += ", "
			
	return speech_output
