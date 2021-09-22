(window.webpackJsonp=window.webpackJsonp||[]).push([[14],{"util/jscharting_utils":function(module,exports,__webpack_require__){var __WEBPACK_AMD_DEFINE_ARRAY__,__WEBPACK_AMD_DEFINE_RESULT__;__WEBPACK_AMD_DEFINE_ARRAY__=[__webpack_require__("require/underscore"),__webpack_require__("helpers/user_agent"),__webpack_require__("models/config"),__webpack_require__("splunk/palettes/ColorCodes"),__webpack_require__("util/console"),__webpack_require__("util/theme_utils"),__webpack_require__("shim/splunk.util"),__webpack_require__("stubs/i18n")],void 0===(__WEBPACK_AMD_DEFINE_RESULT__=function(_,userAgent,configModel,ColorCodes,console,themeUtils,splunkUtils,i18n){var crossBrowserLimit,normalizeLimitAmount=function(limitValue){return parseInt(limitValue,10)||1/0},VISIBLE_FIELD_REGEX=/^[^_]|^_time/,MAX_SERIES=normalizeLimitAmount(splunkUtils.getConfigValue("JSCHART_SERIES_LIMIT",100)),MAX_POINTS=null!==(crossBrowserLimit=splunkUtils.getConfigValue("JSCHART_TRUNCATION_LIMIT",5e4))?normalizeLimitAmount(crossBrowserLimit):userAgent.isFirefox()?normalizeLimitAmount(splunkUtils.getConfigValue("JSCHART_TRUNCATION_LIMIT_FIREFOX",5e4)):userAgent.isSafari()?normalizeLimitAmount(splunkUtils.getConfigValue("JSCHART_TRUNCATION_LIMIT_SAFARI",5e4)):userAgent.isIE11()?normalizeLimitAmount(splunkUtils.getConfigValue("JSCHART_TRUNCATION_LIMIT_IE11",5e4)):normalizeLimitAmount(splunkUtils.getConfigValue("JSCHART_TRUNCATION_LIMIT_CHROME",5e4)),fieldIsVisible=function(field){var fieldName=_.isString(field)?field:field.name;return VISIBLE_FIELD_REGEX.test(fieldName)};return{getCustomDisplayProperties:function(chartData,webConfig){var customProps={};return(webConfig=webConfig||{}).JSCHART_TEST_MODE&&(customProps.testMode=!0),chartData.hasField("_tc")&&(customProps.fieldHideList=["percent"]),customProps},preprocessChartData:function(rawData,displayProperties){if(0===rawData.columns.length||0===rawData.columns[0].length)return rawData;if((displayProperties.chart||"column")in{pie:!0,scatter:!0,radialGauge:!0,fillerGauge:!0,markerGauge:!0})return rawData;if(rawData.fields.length>=MAX_SERIES){var spanColumn,normalizedFields=_(rawData.fields).map(function(field){return _.isString(field)?field:field.name}),spanIndex=_(normalizedFields).indexOf("_span");spanIndex>-1&&spanIndex>=MAX_SERIES&&(spanColumn=rawData.columns[spanIndex]),rawData={columns:rawData.columns.slice(0,MAX_SERIES),fields:rawData.fields.slice(0,MAX_SERIES)},spanColumn&&(rawData.columns.push(spanColumn),rawData.fields.push("_span"))}var perChartLimit=parseInt(displayProperties["chart.resultTruncationLimit"],10)||parseInt(displayProperties.resultTruncationLimit,10),truncationLimit=perChartLimit>0?perChartLimit:MAX_POINTS,numDataSeries=_(rawData.fields).filter(fieldIsVisible).length-1,pointsPerSeries=rawData.columns[0].length,allowedPointsPerSeries=Math.floor(truncationLimit/numDataSeries);return pointsPerSeries>allowedPointsPerSeries?function(rawData,length){var sliced={fields:rawData.fields,columns:[]};return _(rawData.columns).each(function(column,i){sliced.columns[i]=column.slice(0,length)}),sliced}(rawData,allowedPointsPerSeries):rawData},prepareChartingLibrary:function(chartingLib,options){options=options||{},chartingLib.setLoggingConsole(console),"dark"===themeUtils.getCurrentTheme()&&chartingLib.setTheme("dark"),chartingLib.setColorPalette(ColorCodes.CATEGORICAL),chartingLib.setTimezone(options.SERVER_ZONEINFO||configModel.get("SERVER_ZONEINFO")),chartingLib.useSplunkI18nLibrary(i18n)},getSeriesLimit:function(){return MAX_SERIES},setSeriesLimit:function(limit){MAX_SERIES=limit},getTruncationLimit:function(){return MAX_POINTS},setTruncationLimit:function(limit){MAX_POINTS=limit}}}.apply(exports,__WEBPACK_AMD_DEFINE_ARRAY__))||(module.exports=__WEBPACK_AMD_DEFINE_RESULT__)},"views/shared/jschart/Master":function(module,exports,__webpack_require__){var __WEBPACK_AMD_DEFINE_ARRAY__,__WEBPACK_AMD_DEFINE_RESULT__;__WEBPACK_AMD_DEFINE_ARRAY__=[__webpack_require__("shim/jquery"),__webpack_require__("require/underscore"),module,__webpack_require__("models/config"),__webpack_require__("views/shared/viz/Base"),__webpack_require__("util/jscharting_utils"),__webpack_require__("util/general_utils"),__webpack_require__("shim/splunk.util"),__webpack_require__("shim/splunk.legend"),__webpack_require__("uri/route"),__webpack_require__(1421)],void 0===(__WEBPACK_AMD_DEFINE_RESULT__=function($,_,module,configModel,VisualizationBase,jschartingUtils,generalUtils,splunkUtils,SplunkLegend,route,splunkCharting){return _("Invalid timestamp").t(),_("Reset").t(),_("Reset Zoom").t(),_("Pan Right").t(),_("Pan Left").t(),_("No Results").t(),_("Invalid Data").t(),_("Numeric Data Required").t(),_("Invalid data: second column must be numeric for a pie chart").t(),jschartingUtils.prepareChartingLibrary(splunkCharting),VisualizationBase.extend({VIZ_PROPERTY_PREFIX_REGEX:/^display\.visualizations\.charting\./,className:"chart",moduleId:module.i,initialize:function(options){VisualizationBase.prototype.initialize.apply(this,arguments),this.options=options||{},this._selectedRange=null,this.$el.width(this.options.width||"100%"),this.$el.height(this.options.height||"100%"),this.$chart=$("<div></div>"),this.$inlineMessage=$("<div></div>").css("text-align","center").addClass(this.options.messageContainerClass||""),this.computeDisplayProperties(),this.listenTo(this.getPrimaryDataSource(),"destroy",this.empty),this.onExternalPaletteChange=_(this.onExternalPaletteChange).bind(this),this.legendId=(this.options.parentCid||"")+this.cid,SplunkLegend.register(this.legendId),SplunkLegend.addEventListener("labelIndexMapChanged",this.onExternalPaletteChange)},empty:function(){return this.destroyChart(),this.$chart.empty(),this.$inlineMessage.empty(),this},remove:function(){return this.removed=!0,this.destroyChart(),SplunkLegend.unregister(this.legendId),SplunkLegend.removeEventListener("labelIndexMapChanged",this.onExternalPaletteChange),VisualizationBase.prototype.remove.apply(this,arguments)},render:function(){return this.$chart.appendTo(this.el),this.$inlineMessage.appendTo(this.el),VisualizationBase.prototype.render.apply(this,arguments)},onConfigChange:function(changedAttributes){if(_(changedAttributes).chain().keys().any(function(key){return 0===key.indexOf("display.visualizations.charting.")}).value()){this.computeDisplayProperties();var dataRelevantConfigAttributes=["display.visualizations.charting.chart","display.visualizations.charting.chart.resultTruncationLimit","display.visualizations.charting.resultTruncationLimit","display.visualizations.charting.axisY2.enabled","display.visualizations.charting.chart.overlayFields","display.visualizations.charting.chart.stackMode"];_(changedAttributes).any(function(value,key){return _(dataRelevantConfigAttributes).contains(key)})?this.invalidate("formatDataPass"):this.invalidate("updateViewPass")}},combineData:function(dataFromAllSources){return _.extend({},dataFromAllSources.primary,{annotation:dataFromAllSources.annotation})},formatData:function(combinedData){if(!combinedData||!combinedData.columns||0===combinedData.columns.length)return splunkCharting.extractChartReadyData({fields:[],columns:[]});var results=jschartingUtils.preprocessChartData(combinedData,this.displayProperties);results.columns.length>0&&(results.columns.length<combinedData.columns.length||results.columns[0].length<combinedData.columns[0].length)&&(results.areTruncated=!0),combinedData.annotation&&(results.annotations=this.formatAnnotationData(combinedData.annotation));var resultsDataSet=splunkCharting.extractChartReadyData(results);results.areTruncated&&(resultsDataSet.resultsAreTruncated=!0);try{window.__splunk__prepareChartCfgDownload&&window.__splunk__prepareChartCfgDownload(this.cid,JSON.stringify({data:combinedData,props:this.displayProperties},null,2))}catch(e){}return resultsDataSet},formatAnnotationData:function(annotationData){var annotations=[];if(annotationData&&annotationData.columns&&annotationData.columns.length>0){var annotationDataSet=splunkCharting.extractChartReadyData(annotationData);if(annotationDataSet.hasField("_time")){var timeList=annotationDataSet.getSeriesAsTimestamps("_time"),labelList=annotationDataSet.getSeries("annotation_label"),colorList=annotationDataSet.getSeries("annotation_color"),categoryList=annotationDataSet.getSeries("annotation_category");_.each(timeList,function(time,index){annotations.push({time:time,label:labelList[index],color:colorList[index],category:categoryList[index]})},this)}}return annotations},provideScaleValues:function(dataSet,config){if(dataSet.seriesList&&dataSet.seriesList.length>1){var fields=dataSet.getFieldData(),yAxisFields=fields.yFields;if(splunkUtils.normalizeBoolean(config["display.visualizations.charting.axisY2.enabled"])){var overlayFields=splunkUtils.stringToFieldList(config["display.visualizations.charting.chart.overlayFields"]),overlayData=[];_.each(overlayFields,function(field){var index=_.indexOf(dataSet.fields,field);index>-1&&(overlayData=overlayData.concat(dataSet.seriesList[index]))}),yAxisFields=_.difference(fields.yFields,overlayFields)}var yAxisData=[],maxValues=[];if(_.each(yAxisFields,function(field){var index=_.indexOf(dataSet.fields,field);index>-1&&(yAxisData=yAxisData.concat(dataSet.seriesList[index]),maxValues.push(_.max(dataSet.getSeriesAsFloats(field))))}),"stacked"===config["display.visualizations.charting.chart.stackMode"]){var maxValue=_.reduce(maxValues,function(memo,num){return memo+num},0);yAxisData.push(maxValue)}var xAxisData=[];return _.each(fields.xFields,function(field){var index=_.indexOf(dataSet.fields,field);index>-1&&(xAxisData=xAxisData.concat(dataSet.seriesList[index]))}),{xAxis:xAxisData,yAxis:yAxisData,overlayAxis:overlayData}}},updateView:function(dataSet,config,async){var done=async();if(!_.isUndefined(dataSet.seriesList)){splunkCharting.setTimezone(configModel.get("SERVER_ZONEINFO")),this.$inlineMessage.empty();var maxResultCount=this.getPrimaryDataSource().getFetchParams().count;if(dataSet.resultsAreTruncated?this.renderResultsTruncatedMessage():dataSet.seriesList.length>0&&maxResultCount>0&&dataSet.seriesList[0].length>=maxResultCount&&this.renderMaxResultCountMessage(maxResultCount),!_.isUndefined(this.getScale("xAxis")))var xCategories={xCategories:this.getScale("xAxis").get("actualCategories")};if(!_.isUndefined(this.getScale("yAxis"))){var yAxisMin=this.getScale("yAxis").get("actualMinimum"),yAxisMax=this.getScale("yAxis").get("actualMaximum");if(yAxisMin<yAxisMax)var yAxisExtremes={yAxisMin:yAxisMin,yAxisMax:yAxisMax}}if(!_.isUndefined(this.getScale("overlayAxis"))){var overlayAxisMin=this.getScale("overlayAxis").get("actualMinimum"),overlayAxisMax=this.getScale("overlayAxis").get("actualMaximum");if(overlayAxisMin<overlayAxisMax)var overlayAxisExtremes={overlayAxisMin:overlayAxisMin,overlayAxisMax:overlayAxisMax}}var displayProperties=$.extend({},this.displayProperties,jschartingUtils.getCustomDisplayProperties(dataSet,configModel.toJSON()),xCategories,yAxisExtremes,overlayAxisExtremes);this.chart&&_.isEqual(displayProperties,this.chart.getCurrentDisplayProperties())?this.chart.off():(this.destroyChart(),this.chart=splunkCharting.createChart(this.$chart[0],displayProperties)),this.updateChartContainerHeight();var that=this;this.chart.prepare(dataSet,{});var fieldList=this.chart.getFieldList();this.chart.requiresExternalColorPalette()&&(SplunkLegend.setLabels(this.legendId,fieldList),this.externalPalette=this.getExternalColorPalette(),this.chart.setExternalColorPalette(this.externalPalette.fieldIndexMap,this.externalPalette.numLabels)),this.chart.on("pointClick",function(eventInfo){var drilldownEvent=that.normalizeDrilldownEvent(eventInfo,"cell");that.trigger("drilldown",drilldownEvent)}),this.chart.on("legendClick",function(eventInfo){var drilldownEvent;drilldownEvent=eventInfo.hasOwnProperty("name")&&eventInfo.hasOwnProperty("value")?that.normalizeDrilldownEvent(eventInfo,"row"):that.normalizeDrilldownEvent(eventInfo,"column"),that.trigger("drilldown",drilldownEvent)}),this.chart.on("chartRangeSelect",function(eventInfo){var newRange=_(eventInfo).pick("startXIndex","endXIndex","startXValue","endXValue");_.isEqual(newRange,that._selectedRange)||(that._selectedRange=newRange,that.trigger("chartRangeSelect",eventInfo))}),this.chart.draw(function(chart){that.model.config.set({currentChartFields:fieldList},{transient:!0}),done()})}},normalizeDrilldownEvent:function(originalEvent,type){return _.extend({type:type,originalEvent:originalEvent},_(originalEvent).pick("name","value","name2","value2","_span","rowContext","modifierKey"))},getExternalColorPalette:function(){this.synchronizingExternalPalette=!0;var fieldIndexMap={};return _(this.chart.getFieldList()).each(function(field){fieldIndexMap[field]=SplunkLegend.getLabelIndex(field)}),this.synchronizingExternalPalette=!1,{fieldIndexMap:fieldIndexMap,numLabels:SplunkLegend.numLabels()}},onExternalPaletteChange:function(){if(!this.synchronizingExternalPalette){var oldExternalPalette=this.externalPalette;this.externalPalette=this.getExternalColorPalette(),this.chart&&this.chart.requiresExternalColorPalette()&&!_.isEqual(oldExternalPalette,this.externalPalette)&&this.invalidate("updateViewPass")}},destroyChart:function(){this.chart&&(this.chart.off(),this.chart.destroy(),delete this.chart)},reflow:function(){this.chart&&this.$el.height()>0&&(this.updateChartContainerHeight(),this.chart.resize())},updateChartContainerHeight:function(){var messageHeight=this.$inlineMessage.is(":empty")?0:this.$inlineMessage.outerHeight();this.$chart.height(this.$el.height()-messageHeight)},renderResultsTruncatedMessage:function(){var message=_("These results may be truncated. Your search generated too much data for the current visualization configuration.").t();message=this.addTruncationDocsLink(message),this.$inlineMessage.html(_(this.inlineMessageTemplate).template({message:message,level:"warning"}))},renderMaxResultCountMessage:function(resultCount){var message=splunkUtils.sprintf(_("These results may be truncated. This visualization is configured to display a maximum of %s results per series, and that limit has been reached.").t(),resultCount);message=this.addTruncationDocsLink(message),this.$inlineMessage.html(_(this.inlineMessageTemplate).template({message:message,level:"warning"}))},computeDisplayProperties:function(){this.displayProperties={};var jsonConfig=this.model.config.toJSON();_.each(jsonConfig,function(value,key){this.VIZ_PROPERTY_PREFIX_REGEX.test(key)&&(this.displayProperties[key.replace(this.VIZ_PROPERTY_PREFIX_REGEX,"")]=value)},this)},addTruncationDocsLink:function(message){var docsHref=route.docHelp(this.model.application.get("root"),this.model.application.get("locale"),"learnmore.charting.datatruncation");return message+_(' <a href="<%- href %>" target="_blank"><span><%- text %></span><i class="icon-external icon-no-underline"></i></a>').template({href:docsHref,text:_("Learn More").t()})},inlineMessageTemplate:'            <div class="alert alert-inline alert-<%= level %> alert-inline">                 <i class="icon-alert"></i>                 <%= message %>             </div>         '})}.apply(exports,__WEBPACK_AMD_DEFINE_ARRAY__))||(module.exports=__WEBPACK_AMD_DEFINE_RESULT__)}}]);