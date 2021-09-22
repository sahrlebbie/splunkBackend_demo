// A helper that defines Token Filter, Token Fowarder, create local token caches, and reset relevant token values for AWS App.
define([
    'splunkjs/mvc',
    'splunkjs/mvc/tokenforwarder',
    'app/splunk_app_aws/js/swc-aws/index',
], function(mvc, TokenForwarder, index) {
    'use strict';

    const utils = index.utils;
    const splunkd_utils = index.splunkd_utils;
    const TAG_PREFIX = /\$PREFIX\$/g;
    const DETAILED_DATA_MODEL = 'detailed_billing';
    const INSTANCE_DATA_MODEL = 'instance_hour';
    const DETAILED_DATA_MODEL_CUR = 'detailed_billing_cur';
    const INSTANCE_DATA_MODEL_CUR = 'instance_hour_cur';
    const COUNT_SPL = 'timechart sum(count) as "Instance Hours" span=1d';
    const COUNT_CUR_SPL = 'timechart sum(count) as "Instance Hours" span=1d';
    const COST_SPL = `timechart span=1d sum(cost) as "Cost"`;
    const CURRENCY_MAP = {
        'USD': '$',
        'CNY': '¥',
        'JPY': '¥',
        'EUR': '€'
    };

    let tokenModel = mvc.Components.getInstance("default");

    let createLocalStorageToken = function(localName, tokenName, forwarderFunc) {
        if (tokenModel.get('disableLocalToken')) {
            return null;
        }
        tokenModel.on(`change:${tokenName}`, function(model, value) {
            if (typeof value === undefined || value === undefined) {
                value = '*';
            }
            localStorage.setItem(localName, value);
        });

        let localValue = localStorage.getItem(localName) || '*';
        tokenModel.set(localName, localValue);

        new TokenForwarder([`$${localName}$`], `$${tokenName}$`, forwarderFunc);
    };

    mvc.setFilter('currency2Symbol', (currency) => {
        if (currency) {
            if (currency in CURRENCY_MAP) {
                return CURRENCY_MAP[currency];
            } else {
                return '';
            }
        }
    });
     
    ['countspl', 'costspl'].forEach(function(type) {

        mvc.setFilter(`groupby2${type}`, function(inputValue) {
            let spl = (type === 'countspl' ? COUNT_SPL : COST_SPL);
            let model = (type === 'countspl' ? INSTANCE_DATA_MODEL : DETAILED_DATA_MODEL);
            if (inputValue && inputValue.length > 0) {
                switch (inputValue) {
                    case 'none':
                        return `by _time span=1d | ${spl}`;
                    case 'reservation':
                        return `by _time ${INSTANCE_DATA_MODEL}.ReservedInstance span=1d | eval Reserved=if('instance_hour.ReservedInstance'="Y", count, 0) | eval count=if('instance_hour.ReservedInstance'="N", count, 0) | fields _time count Reserved | timechart sum(count) as "On-demand" sum(Reserved) as Reserved span=1d`;
                    default:
                        return `by _time ${model}.${inputValue} span=1d | eval ${model}.${inputValue}=if('${model}.${inputValue}'=="", "No Value", '${model}.${inputValue}') | ${spl} by ${model}.${inputValue}`;
                }
            } else {
                return inputValue;
            }
        });

        mvc.setFilter(`curgroupby2${type}`, function(inputValue) {
            let spl = (type === 'countspl' ? COUNT_CUR_SPL : COST_SPL);
            let model = (type === 'countspl' ? INSTANCE_DATA_MODEL_CUR : DETAILED_DATA_MODEL_CUR);
            if (inputValue && inputValue.length > 0) {
                switch (inputValue) {
                    case 'none':
                        return `by _time span=1d | ${spl}`;
                    case 'reservation':
                        return `by _time ${INSTANCE_DATA_MODEL_CUR}.ReservedInstance span=1d | eval Reserved=if('instance_hour_cur.ReservedInstance'="Y", count, 0) | eval count=if('instance_hour_cur.ReservedInstance'="N", count, 0) | fields _time count Reserved | timechart sum(count) as "On-demand" sum(Reserved) as Reserved span=1d`;
                    default:
                        return `by _time ${model}.${inputValue} span=1d | eval ${model}.${inputValue}=if('${model}.${inputValue}'=="", "No Value", '${model}.${inputValue}') | ${spl} by ${model}.${inputValue}`;
                }
            } else {
                return inputValue;
            }
        });
    });
    
   
    mvc.setFilter('costbygroups', function(inputValue) {
        if (inputValue && inputValue.length > 0) {
            let values = inputValue.split('|');
            let by = values.map(value => {
                return `${DETAILED_DATA_MODEL}.${value}`;
            }).join(' ');
            let rename = values.map(value => {
                return `${DETAILED_DATA_MODEL}.${value} as ${value}`;
            }).join(', ');

            return `by ${by} | rename ${rename}`;
        } else {
            return inputValue;
        }
    });
	mvc.setFilter('curcostbygroups', function(inputValue) {
        if (inputValue && inputValue.length > 0) {
            let values = inputValue.split('|');
            let by = values.map(value => {
                return `${DETAILED_DATA_MODEL_CUR}.${value}`;
            }).join(' ');
            let rename = values.map(value => {
                return `${DETAILED_DATA_MODEL_CUR}.${value} as ${value}`;
            }).join(', ');

            return `by ${by} | rename ${rename}`;
        } else {
            return inputValue;
        }
    });


    let createConverter = function(mapFunc, returnFunc, separator = ',', joinStr = ' OR ') {
        return function(input) {
            if (input && input.length > 0) {
                let result = input.split(separator)
                    .map(mapFunc)
                    .join(joinStr);

                return returnFunc(result);
            } else {
                return input;
            }
        };
    };


    // Used in individual Instance/EBS dashboard. Convert id to metric_dimensions for CloudWatch, or to Description.
    mvc.setFilter(`id2InstanceId`,
        createConverter(
            id => `metric_dimensions="InstanceId=[${id}]"`,
            result => `(${result})`
        )
    );

    mvc.setFilter(`id2VolumeId`,
        createConverter(
            id => `metric_dimensions="VolumeId=[${id}]"`,
            result => `(${result})`
        )
    );

    mvc.setFilter('id2description',
        createConverter(
            id => `id="${id}"`,
            result => `(${result})`
        )
    );

    // Used in Tags filter. Convert tags to Description, Config, and Billing
    ['tag2description', 'tag2config'].forEach(filterName => {
        mvc.setFilter(filterName,
            createConverter(
                tag => tag.replace(TAG_PREFIX, 'tags.'),
                result => `|search ${result}`,
                '||',
                ' AND '
            )
        );
    });

    mvc.setFilter('tag2notification',
        createConverter(
            tag => tag.replace(TAG_PREFIX, 'configurationItem.tags.'),
            result => `|search ${result}`,
            '||',
            ' AND '
        )
    );

    mvc.setFilter('tag2billing',
        createConverter(
            tag => {
                tag = tag.replace(TAG_PREFIX, 'user:');
                return `"${tag}"`;
            },
            result => `|search ${result}`,
            '||',
            ' AND '
        )
    );

    mvc.setFilter('tag2detailed_billing',
        createConverter(
            tag => tag = tag.replace(TAG_PREFIX, 'detailed_billing.'),
            result => result,
            '||',
            ' AND '
        )
    );

    mvc.setFilter('tag2detailed_billing_cur',
        createConverter(
            tag => tag = tag.replace(TAG_PREFIX, 'detailed_billing_cur.'),
            result => result,
            '||',
            ' AND '
        )
    );

    mvc.setFilter('tag2instance_hour',
        createConverter(
            tag => tag = tag.replace(TAG_PREFIX, 'instance_hour.'),
            result => result,
            '||',
            ' AND '
        )
    );

    mvc.setFilter('tag2instance_hour_cur',
        createConverter(
            tag => tag = tag.replace(TAG_PREFIX, 'instance_hour_cur.'),
            result => result,
            '||',
            ' AND '
        )
    );
    
    mvc.setFilter('tag2topology', function(inputValue) {
        if (inputValue && inputValue.length > 0) {
            let tags = inputValue.split(' OR ');
            let result = '| fillnull value=\"\" tags | search ';
            for(let i = 0; i<tags.length; i++){
                let tag = tags[i].replace(TAG_PREFIX, ''),
                    arr = tag.split('='),
                    key = arr[0],
                    value = arr[1],
                    isContains=false,
                    isEmpty=false;
                if(key.substr(0,3) === 'NOT') {
                    isEmpty = true;
                    key = key.substr(4);
                }
                else if(value[1] ===  '*' && value[value.length-2] === '*') {
                    isContains = true;
                }
                value = value.substring(1, value.length-1);
                if(isContains) {
                    value = value.substring(1, value.length-1);
                    result += "tags=\"\\S*"+key+",\\S*"+value+"\\S*\"";
                }
                else if(isEmpty) {
                    result += "tags=\"^(?!.*"+key+",)\"";
                }
                else 
                {
                        var newar = tag.split('=');
                        if (tag.search('AND')==-1)
                        {
                            result+="(tags=\"*"+newar[0]+","+newar[1].slice(1, newar[1].length-1)+"*\")";
                        }
                        if(tag.search('AND')!=-1)
                        {
                            var andarr = tag.split(' AND ');
                            for (let j=0;j<andarr.length;j++)
                            {
                                var andsplit = andarr[j].split('=');
                                result+="(tags=\"*"+andsplit[0]+","+andsplit[1].slice(1, andsplit[1].length-1)+"*\")";
                                if(j!=andarr.length-1)
                                {
                                    result+=" AND ";
                                }
                            }
                        }
                }
                if(i!=tags.length-1)
                {
                    result+=" OR ";
                }

            }
            return result;
        } else {
            return inputValue;
        }
    });

    return {
        createLocalStorageToken: createLocalStorageToken,

        resetTokenValue: function(sourceTokenName, targetTokenName, targetTokenValue) {
            tokenModel.on(`change:${sourceTokenName}`, function(){
                tokenModel.set(targetTokenName, targetTokenValue);
            });
        }
    }
});
