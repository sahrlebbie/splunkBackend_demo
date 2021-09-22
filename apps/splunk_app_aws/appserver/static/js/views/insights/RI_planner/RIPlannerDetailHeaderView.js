define([
    'app/splunk_app_aws/js/libs/underscore',
    'app/splunk_app_aws/js/libs/backbone',
    'app/splunk_app_aws/js/swc-aws/index',
    'app/views/insights/RI_planner/RIPlannerDetailInfoView',
    'app/views/insights/RI_planner/RIPlannerDetailFiltersView'
], function (_, Backbone, index, infoView, filtersView) {
    const BaseView = index.BaseView;
    return BaseView.extend({

        initialize: function () {
            BaseView.prototype.initialize.apply(this, arguments);
            this.listenTo(this.model, 'change:filtersEnabled', this._changeFiltersState.bind(this));
        },

        _changeFiltersState: function () {
            if (this.model.get('filtersEnabled')) {
                this.filterView.enableFilters();
            } else {
                this.filterView.disableFilters();
            }
        },
        render: function () {
            this.$el.html(`<div id='infoContainer'></div><div id='filterContainer'></div>`);
            this.infoView = new infoView({
                el: this.$('#infoContainer')
            }).render();
            this.filterView = new filtersView({
                el: this.$('#filterContainer')
            }).render();
            return this;
        }
    });
});
