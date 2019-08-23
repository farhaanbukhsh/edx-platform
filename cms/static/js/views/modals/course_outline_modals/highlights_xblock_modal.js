/**
 * This is the highlights XBlock modal implementation
 */
define(['underscore', 'gettext', 'edx-ui-toolkit/js/utils/string-utils',
  'js/views/modals/course_outline_modals/xblock_modal',
], function (
  _, gettext, StringUtils, CourseOutlineXBlockModal
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
        this.options.modalName = 'highlights-' + this.options.xblockType;
      }
    },

    getTitle: function () {
      return StringUtils.interpolate(
        gettext('Highlights for {display_name}'),
        {display_name: this.model.get('display_name')}
      );
    },

    getIntroductionMessage: function () {
      return '';
    },

    callAnalytics: function (event) {
      event.preventDefault();
      window.analytics.track('edx.bi.highlights.' + event.target.innerText.toLowerCase());
      if (event.target.className.indexOf('save') !== -1) {
        this.save(event);
      } else {
        this.hide();
      }
    },

    addActionButtons: function () {
      this.addActionButton('save', gettext('Save'), true);
      this.addActionButton('cancel', gettext('Cancel'));
    }
  });
});
