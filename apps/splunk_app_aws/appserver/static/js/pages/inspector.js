define([
  'app/splunk_app_aws/js/libs/underscore',
  'app/splunk_app_aws/js/libs/jquery',
  "splunkjs/mvc",
  "app/splunk_app_aws/js/swc-aws/index",
  "splunkjs/mvc/checkboxview",
  "splunkjs/mvc/searchmanager",
  "splunkjs/mvc/simplexml/element/table",
  "splunkjs/mvc/tableview",
  "appcss/pages/inspector/bootstrap.pcss",
  'app/views/dashboard/common',
  "splunkjs/mvc/simplexml/ready!"
], function(
  _,
  $,
  mvc,
  index,
  CheckboxView,
  SearchManager,
  TableElement,
  TableView
) {
  "use strict";
  const utils = index.utils;
  const TokenUtils = index.TokenUtils;

  // Render the "Findings" panel
  // "title", "description", "recommendation" fields are hidden by inspector/bootstrap.pcss
  new SearchManager({
    "id": "search_findings",
    "earliest_time": "0",
    "latest_time": "now",
    "status_buckets": 0,
    "auto_cancel": 90,
    "preview": true,
    "search":
      '`aws-inspector-findings` ' +
      'serviceAttributes.assessmentRunArn="$runArn$" ' +
      '`aws-inspector-rex-arn` ' +
      '| search $accountId$ $region$' +
      '| dedup arn' +
      '| search $severityFilter$' +
      '| spath OUTPUT=agentId assetAttributes.agentId ' +
      '$findingsFilter$' +
      '| eval CreatedAt=substr(createdAt, 1, 19) ' +
      '| join type="left" serviceAttributes.rulesPackageArn [search `aws-inspector-runs` arn="$runArn$" | dedup rulesPackages{}.arn ' +
      '| rename rulesPackages{}.arn as packageArn, rulesPackages{}.name as packageName' +
      '| eval row=mvzip(packageArn, packageName, "|") ' +
      '| mvexpand row | rex field=row "(?<packageArn>.*?)\\|(?<packageName>.*)" ' +
      '| table packageArn packageName | rename packageArn as "serviceAttributes.rulesPackageArn"]' +
      '| rename packageName as "Rules Package"' +
      '| eval Links = if(isnotnull(agentId), "<a id=topology_link>Show in Topology</a> | <a id=ec2_link>Show Instance Details</a>", "") ' +
      '| sort -numericSeverity ' +
      '| join agentId type="left" [search earliest=-1d `aws-description-resource((aws_account_id="*"),  (region="*") , "*")`| rename id as agentId ] ' +
      '| rename severity as Severity, id as Rule,  agentId as "EC2 Instance ID", tags.Name as "EC2 Instance Name"' +
      '| fillnull value="N/A" ' +
      '| table Severity, "EC2 Instance ID", "EC2 Instance Name", "Rules Package", Rule, CreatedAt, Links, title, description, recommendation'
  }, {tokens: true});

  var findingsTable = new TableElement({
    "id": "findings-table",
    "count": 10,
    "dataOverlayMode": "none",
    "drilldown": "cell",
    "rowNumbers": "false",
    "wrap": "true",
    "managerid": "search_findings",
    "el": $('#findings_table')
  }, {tokens: true});

findingsTable.on("create:visualization", function() {
  findingsTable.visualization.addCellRenderer(
    new (TableView.BaseCellRenderer.extend({
      canRender: function(cellData) {
        return cellData.field === "Links";
      },

      render: function($td, cellData) {
        $td.html(cellData.value);
      }
    }))()
  );

  findingsTable.visualization.addRowExpansionRenderer(
    new (TableView.BaseRowExpansionRenderer.extend({
      canRender: function() {
        return true;
      },

      render: function($container, rowData) {
        var fields = rowData.fields,
          values = rowData.values;

        $container.append(
          '<dl>' +
            '<dt>Finding</dt>' +
            '<dd>' + values[fields.indexOf('title')] + '</dd>' +
            '<dt>Description</dt>' +
            '<dd>' + values[fields.indexOf('description')] + '</dd>' +
            '<dt>Recommended Action</dt>' +
            '<dd>' + values[fields.indexOf('recommendation')] + '</dd>' +
            '</dl>'
        );
      }
    }))()
  );
});
  findingsTable.render();

  findingsTable.on("click", function(e) {
    e.preventDefault();

    var defaultTokenModel = mvc.Components.getInstance("default");

    if (e.event.originalEvent.target.tagName.toLowerCase() === 'a') {
      let target = e.event.originalEvent.target;
      if (target.id === "topology_link") {
        let url = TokenUtils.replaceTokenNames("topology?resourceId=$row.EC2 Instance ID$&layers.inspectorLayer=true&form.state=*&form.accountId=*&form.region=*&form.vpc=*&disableLocalToken=true", _.extend(defaultTokenModel.toJSON(), e.data), TokenUtils.getEscaper('url'));
        utils.redirect(url);
      } else if (target.id === "ec2_link") {
        let url = TokenUtils.replaceTokenNames("individual_instance_usage?form.accountId=*&form.instances=$row.EC2 Instance ID$", _.extend(defaultTokenModel.toJSON(), e.data), TokenUtils.getEscaper('url'));
        utils.redirect(url);
      }
    }
  });

  function hideOKFindings() {
    mvc.Components.get("default").set("findingsFilter", "| where isnotnull(agentId)");
  }

  function showOKFindings() {
    mvc.Components.get("default").set("findingsFilter", "");
  }

  var findingsFilterChkBox = new CheckboxView({
    id: "findings-filter-chkbox",
    default: true,
    el: $("#findings_filter_chkbox")
  })
  findingsFilterChkBox.render();
  $('#findings_filter_chkbox')
    .css('margin-left', '10px')
    .css('min-width', '280px')
    .css('margin-top', '24px');
  $('#findings_filter_chkbox').find('[data-component="splunk-core:/splunkjs/mvc/components/Checkbox"]')
    .css('display', 'inline-block');
  $('#findings_filter_chkbox')
    .append('<span style="margin-left: 5px;">Hide findings without security issues</span>');

  // Handle "Hide non-issues" checkbox
  findingsFilterChkBox.on("change", function(checked) {
    if(checked) {
      hideOKFindings();
    } else {
      showOKFindings();
    }
  });

  // default
  hideOKFindings();

});
