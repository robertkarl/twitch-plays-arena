/**
 *    Copyright 2019 Amazon.com, Inc. or its affiliates
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

var twitch = window.Twitch ? window.Twitch.ext : null;
var doshit = $('#justabutton');
twitch.rig.log('hello rig');
doshit.click(function() {
  twitch.rig.log('button click received');
  // TODO: post coords of click.
});

function post_some_shit() {



(function () {

    var tuid = "";
    // The Twitch JavaScript Helper must be initialized
    if (!twitch) {
        return;
    }

    // Twitch onAuthorized callback
    // We will not use the JWT here, as we need a JWT from the broadcaster instead of the viewer.
    // Reference: https://dev.twitch.tv/docs/extensions/reference/#onauthorized
    twitch.onAuthorized(function (auth) {
        tuid = auth.userId
        log("onAuhorized() fired\nUser " + tuid + " started extension");
    });

    // Listen for an incoming PubSub message and adjust HTML elements accordingly
    // Reference: https://dev.twitch.tv/docs/extensions/reference/#listen
    twitch.listen('broadcast', function (_target, _contentType, message) {
        log("listen() fired, PubSub message received, giveawayInProgress: " + message);
    });
})()
