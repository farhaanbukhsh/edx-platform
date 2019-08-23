/**
 * This is a base XBlock modal implementation that provides common utilities for creating editors.
 */
define(['jquery', 'underscore',
  'js/views/modals/base_modal', 'js/views/utils/xblock_utils'
], function (
  $, _, BaseModal, XBlockViewUtils
) {
  'use strict';
  return BaseModal.extend({
    events: _.extend({}, BaseModal.prototype.events, {
      'click .action-save': 'save',
      keydown: 'keyHandler'
    }),

    options: $.extend({}, BaseModal.prototype.options, {
      modalName: 'course-outline',
      modalType: 'edit-settings',
      addPrimaryActionButton: true,
      modalSize: 'med',
      viewSpecificClasses: 'confirm',
      editors: []
    }),

    initialize: function () {
      BaseModal.prototype.initialize.call(this);
      this.template = this.loadTemplate('course-outline-modal');
      this.options.title = this.getTitle();
    },

    afterRender: function () {
      BaseModal.prototype.afterRender.call(this);
      this.initializeEditors();
    },

    initializeEditors: function () {
      this.options.editors = _.map(this.options.editors, function (Editor) {
        return new Editor({
          parentElement: this.$('.modal-section'),
          model: this.model,
          xblockType: this.options.xblockType,
          enable_proctored_exams: this.options.enable_proctored_exams,
          enable_timed_exams: this.options.enable_timed_exams
        });
      }, this);
    },

    getTitle: function () {
      return '';
    },

    getIntroductionMessage: function () {
      return '';
    },

    getContentHtml: function () {
      return this.template(this.getContext());
    },

    save: function (event) {
      var requestData;

      event.preventDefault();
      requestData = this.getRequestData();
      if (!_.isEqual(requestData, {metadata: {}})) {
        XBlockViewUtils.updateXBlockFields(this.model, requestData, {
          success: this.options.onSave
        });
      }
      this.hide();
    },

    /**
     * Return context for the modal.
     * @return {Object}
     */
    getContext: function () {
      return $.extend({
        xblockInfo: this.model,
        introductionMessage: this.getIntroductionMessage(),
        enable_proctored_exams: this.options.enable_proctored_exams,
        enable_timed_exams: this.options.enable_timed_exams
      });
    },

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

    keyHandler: function (event) {
      if (event.which === 27) {  // escape key
        this.hide();
      }
    }
  });
});
