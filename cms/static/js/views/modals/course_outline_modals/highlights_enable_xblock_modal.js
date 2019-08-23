/**
 * This is the highlights enabling XBlock modal implementation
 */
define(['underscore', 'gettext', 'js/views/modals/course_outline_modals/xblock_modal',
], function (
  _, gettext, CourseOutlineXBlockModal
) {
  'use strict';
  return CourseOutlineXBlockModal.extend({

    events: _.extend({}, CourseOutlineXBlockModal.prototype.events, {
      'click .action-save': 'callAnalytics',
      'click .action-cancel': 'callAnalytics'
    }),

    initialize: function () {
      CourseOutlineXBlockModal.prototype.initialize.call(this);
      if (this.options.xblockType) {
        this.options.modalName = 'highlights-enable-' + this.options.xblockType;
      }
    },

    getTitle: function () {
      return gettext('Enable Weekly Highlight Emails');
    },

    getIntroductionMessage: function () {
      return '';
    },

    callAnalytics: function (event) {
      event.preventDefault();
      window.analytics.track('edx.bi.highlights_enable.' + event.target.innerText.toLowerCase());
      if (event.target.className.indexOf('save') !== -1) {
        this.save(event);
      } else {
        this.hide();
      }
    },

    addActionButtons: function () {
      this.addActionButton('save', gettext('Enable'), true);
      this.addActionButton('cancel', gettext('Not yet'));
    }
  });
});
