/* eslint-disable  func-names */
/* eslint quote-props: ["error", "consistent"]*/

'use strict';
var rq = require('request-promise');
const Alexa = require('alexa-sdk');
const APP_ID = 'amzn1.ask.skill.88ac4a4d-461b-4a38-a9da-c7a15dde3000';

const WELCOME_MESSAGE = 'Would you like an update from your home network, or information on a specific device?';
const WELCOME_REPROMPT = 'Say please say help me, for a list of commands.';

const HELP_MESSAGE = 'Ask me for an update, or information on devices, alerts, or destinations.';
const STOP_MESSAGE = 'Goodbye!';

const ITEM_NOT_FOUND = 'I\'m sorry, I don\'t think we sell that item. Please try another one.';

const handlers = {
    'LaunchRequest': function () {
        this.response.speak(WELCOME_MESSAGE).listen(WELCOME_REPROMPT);
        this.emit(':responseReady');
    },
    'Digest': function () {
        var updateText = 'Default';
		var context = this;
		var options = {uri: 'https://wseymour.co.uk/alexa/digest.json', json: true}
        
		rq(options)
		.then(function(response){
            console.log(response);
			updateText = response;
        })
		.catch(function(error){
			updateText = 'Error while contacting refine';
			console.log(error);
		})
		.finally(function(){
        	context.response.speak(updateText);
        	context.emit(':responseReady');
		});
    },
    'SpecificDevice': function() {
        const itemSlot = this.event.request.intent.slots.device.value;
		var message = ''
        var context = this;
		var options = {uri: 'https://wseymour.co.uk/alexa/destination-fridge.json', json: true}
		const prefix = ['The most popular destination for this device was ', ', followed by ', ', and ']

		rq(options)
		.then(function(response){
			//var res = JSON.parse(response);
			var results = response.results;
			var total = response.total;
			var i = 0;
			var first = JSON.parse('{"name":"","impact":0}');
			var second = JSON.parse('{"name":"","impact":0}');
			var third = JSON.parse('{"name":"","impact":0}');
			
			while (i < results){
				if (response.destinations[i].impact > first.impact) {first = response.destinations[i];}
				else if (response.destinations[i].impact > second.impact) {second = response.destinations[i];}
				else if (response.destinations[i].impact > third.impact) {third = response.destinations[i];}
				i++;
			}

			message = prefix[0] + first.name + ' with ' + Math.round((first.impact / total)*100) + '% of traffic';
			message += prefix[1] + second.name + ' with ' + Math.round((second.impact / total)*100) + '%';
			message += prefix[2] + third.name + ' with ' + Math.round((third.impact / total)*100) + '%';
		}).catch(function(error){
			message = 'There was a problem contacting refine';
			console.log(error);
		}).finally(function(){
			context.response.speak(message);
			context.emit(':responseReady');
		});
    },
    'AMAZON.HelpIntent': function () {
        this.response.speak(HELP_MESSAGE).listen(HELP_MESSAGE);
        this.emit(':responseReady');
    },
    'AMAZON.StopIntent': function () {
        this.response.speak(STOP_MESSAGE);
        this.emit(':responseReady');
    },
    'AMAZON.CancelIntent': function () {
        this.response.speak(STOP_MESSAGE);
        this.emit(':responseReady');
    },
    'Unhandled': function () {
        this.response.speak("These are not the functions you're looking for.").listen(HELP_MESSAGE);
        this.emit(':responseReady');
    },
};

exports.handler = function (event, context, callback) {
    const alexa = Alexa.handler(event, context, callback);
    alexa.APP_ID = APP_ID;
    alexa.registerHandlers(handlers);
    alexa.execute();
};
