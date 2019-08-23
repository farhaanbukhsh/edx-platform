/**
 * This is the settings XBlock modal implementation
 */
define(['jquery', 'underscore', 'gettext', 'edx-ui-toolkit/js/utils/string-utils', 'edx-ui-toolkit/js/utils/html-utils',
  'js/views/modals/course_outline_modals/xblock_modal',
], function (
  $, _, gettext, StringUtils, HtmlUtils, CourseOutlineXBlockModal
) {
  'use strict';
  return CourseOutlineXBlockModal.extend({

    getTitle: function () {
      return StringUtils.interpolate(
        gettext('{display_name} Settings'),
        {display_name: this.model.get('display_name')}
      );
    },

    initializeEditors: function () {
      var tabs = this.options.tabs;
      if (tabs && tabs.length > 0) {
        if (tabs.length > 1) {
          var tabsTemplate = this.loadTemplate('settings-modal-tabs');
          HtmlUtils.setHtml(this.$('.modal-section'), HtmlUtils.HTML(tabsTemplate({tabs: tabs})));
          _.each(this.options.tabs, function (tab) {
            this.options.editors.push.apply(
              this.options.editors,
              _.map(tab.editors, function (Editor) {
                return new Editor({
                  parent: this,
                  parentElement: this.$('.modal-section .' + tab.name),
                  model: this.model,
                  xblockType: this.options.xblockType,
                  enable_proctored_exams: this.options.enable_proctored_exams,
                  enable_timed_exams: this.options.enable_timed_exams
                });
              }, this)
            );
          }, this);
          this.showTab(tabs[0].name);
        } else {
          this.options.editors = tabs[0].editors;
          CourseOutlineXBlockModal.prototype.initializeEditors.call(this);
        }
      } else {
        CourseOutlineXBlockModal.prototype.initializeEditors.call(this);
      }
    },

    events: _.extend({}, CourseOutlineXBlockModal.prototype.events, {
      'click .action-save': 'save',
      'click .settings-tab-button': 'handleShowTab'
    }),

    /**
     * Return request data.
     * @return {Object}
     */
    getRequestData: function () {
      var requestData = _.map(this.options.editors, function (editor) {
        return editor.getRequestData();
      });
      return $.extend.apply(this, [true, {}].concat(requestData));
    },

    handleShowTab: function (event) {
      event.preventDefault();
      this.showTab($(event.target).data('tab'));
    },

    showTab: function (tab) {
      this.$('.modal-section .settings-tab-button').removeClass('active');
      this.$('.modal-section .settings-tab-button[data-tab="' + tab + '"]').addClass('active');
      this.$('.modal-section .settings-tab').hide();
      this.$('.modal-section .' + tab).show();
    }
  });
});
