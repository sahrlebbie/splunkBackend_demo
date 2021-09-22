"use strict";

define([
  'app/splunk_app_aws/js/libs/underscore',
  "app/splunk_app_aws/js/swc-aws/index"
], function(
  _,
  index
) {
  const Utils = index.utils;
  return {
    getLogoImg: function(engine) {
      var src;
      engine = engine.toLowerCase();
      switch(engine) {
        case "postgres":
          src = "postgresql.png";
          break;
        case "mysql":
          src = "mysql.svg";
          break;
        case "mariadb":
          src = "mariadb.png";
          break;
        default:
          if(engine.indexOf("oracle") > -1) {
            src = "oracle.svg";
          } else if(engine.indexOf("sqlserver") > -1) {
            src = "sql_server.svg";
          }
      }

      if(_.isUndefined(src)) { return ""; }

      return `<img class="rds_logo" src="/en-US/static/app/${Utils.getCurrentApp()}/img/logos/${src}"/>`;
    }
  };
});
