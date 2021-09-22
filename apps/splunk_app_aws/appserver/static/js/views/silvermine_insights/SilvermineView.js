define([
    'app/splunk_app_aws/js/libs/jquery',
    'app/splunk_app_aws/js/libs/backbone',
    'app/splunk_app_aws/js/swc-aws/index',
    'app/views/silvermine_insights/components/SilvermineHeader',
    'app/views/silvermine_insights/components/SilvermineTable',
], ( $, Backbone, index, SilvermineHeader, SilvermineTable) => {
    const BaseView = index.BaseView;
    return BaseView.extend({
        className: 'silvermine-view',

        initialize: function(params){
            BaseView.prototype.initialize.apply(this, arguments);

            // Managerid is used in SilvermineTable
            this.managerid = params.managerid;

            // Initialize model
            this.model = params.model;
        },

        render:function(){
            this.$el.empty();

            // Render silvermine header
            let silvermineView = new SilvermineHeader({model: this.model});
            this.$el.append(silvermineView.render().$el);

            // Render silvermine table
            let silvermineTable = new SilvermineTable({managerid: this.managerid, model: this.model});
            this.$el.append(silvermineTable.render().$el);

            return this;
        }

    })
});
