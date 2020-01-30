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
var body = $('#body');
twitch.rig.log('hello rig');
body.click(function(e) {
  twitch.rig.log('button click received');
  var x = e.pageX;
  var y = e.pageY;
  var width = window.innerWidth;
  var height = window.innerHeight;
  var s = x + ', ' + y;
  var viewport = width + ', ' + height;
  twitch.rig.log(s);
  twitch.rig.log('viewport is ' + viewport);
  $('#txt').html('voted for ' + s);
  var params = $.param({
    x: x,
    y: y,
    width: width,
    height: height,
    id: window.tuid
  });

  $.post('http://localhost:5000/vote?' + params,
      function() {
          $('#txt').html(s);
          twitch.rig.log('post succeeded');
      }
  );
});

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
        tuid = auth.userId;
        window.tuid = tuid;
        log("onAuhorized() fired\nUser " + tuid + " started extension");
    });

})()
