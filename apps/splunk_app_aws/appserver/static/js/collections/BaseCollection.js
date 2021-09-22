/**
 * Created by michael on 6/21/15.
 */
define([
    'app/splunk_app_aws/js/swc-aws/index'
], function(index) {

    const SplunkDsBaseCollection = index.SplunkDsBaseCollection;

    return SplunkDsBaseCollection.extend({
        fetch: function () {
            var self = this;
            var promise = SplunkDsBaseCollection.prototype.fetch.apply(this, arguments);
            promise.done(function () {
                self._fetched = true;
            });
            return promise;
        },
        isFetched: function () {
            return this._fetched === true;
        }
    });
});
