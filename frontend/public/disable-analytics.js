// Disable all analytics and recording scripts
(function() {
  'use strict';
  
  // Block PostHog
  if (window.posthog) {
    try {
      window.posthog.opt_out_capturing();
      window.posthog = undefined;
    } catch (e) {}
  }
  
  // Block rrweb
  if (window.rrweb) {
    try {
      if (window.rrweb.record && window.rrweb.record.stop) {
        window.rrweb.record.stop();
      }
      window.rrweb = undefined;
    } catch (e) {}
  }
  
  // Prevent future initialization
  Object.defineProperty(window, 'posthog', {
    get: function() { return undefined; },
    set: function() {},
    configurable: false
  });
  
  Object.defineProperty(window, 'rrweb', {
    get: function() { return undefined; },
    set: function() {},
    configurable: false
  });
  
  console.log('✅ Analytics and recording scripts disabled');
})();
