/* PlotWrapper: A Class wraps flot api to enable drawing multiple series in 
 * one chart additively.
 */


/* Check dependencies.
 */
//var jQuery;
if(!jQuery || typeof jQuery != 'function')
    throw new Error('jquery.js has not been loaded');
if(!defineClass || typeof defineClass != 'function')
    throw new Error('utils.js has not been loaded');


/**
 * DataSeries: the helper class for PlotWrapper to hold temporary data.
 * The argument to the constructor can either be a string representing
 * the name of series or an object specifies option attributes. 
 * 
 * An example of object argument:
 * { name: 'line1',
 *   series: { label: 'y = x + 1',
 *             color: 'red',
 *             data: [[0,1], [1,2], [2,3]] }}
 */
var DataSeries = defineClass({
    construct: function(args) {
        this.name = (typeof(args) == 'string') ? args : args.name;
        //this.maxRange = args.maxRange || 0;
        this.rawSeries = args.series || {};
        //if(!this.rawSeries.label) this.rawSeries.label = this.name;
        if(!this.rawSeries.data) this.rawSeries.data = [];
        var extras = args.extras || {};
        for(var p in extras) 
            if (!(p in this)) this[p] = extras[p];
    },
    methods: {
        appendData: function(rawdata) {
            this.rawSeries.data = this.rawSeries.data.concat(rawdata);
        }
    }
});


/**
 * PlotWrapper: A Class wraps flot api to enable drawing multiple series in 
 * one chart additively.
 *
 * An example of object argument:
 * { placeholder: 'placeholder',
 *   data: [ds1, new DataSource('line2')],
 *   onDataSeriesUpdate: function(event) {} }
 */
var PlotWrapper = defineClass({
    construct: function(args) {
        this.canvas = (typeof(args) == 'string') ? jQuery('#' + args): 
            ((typeof(args.placeholder) == 'string') ? jQuery('#' + args.placeholder) :
             args.placeholder);
        this.data = {};
        this.rawSeries = [];
        this.options = args.options || {};
        this.maxRange = args.maxRange || 0;
        
        // if maxRange > 0 then this is a fixed length plot.
        if(this.maxRange > 0) {
            jQuery(this).bind('dataSeriesUpdate', function(e, dataSeries) {
                var rawdata = dataSeries.rawSeries.data;
                var len = rawdata.length;
                if(len) {
                    var first = rawdata[0][0];
                    if(!this.min || this.min > first) {
                        this.min = first;
                    }
                    var last = rawdata[len - 1][0];
                    if(!this.max || this.max < last) {
                        this.max = last;
                    }
                    //console.log('max: ' + this.max);
                    if(this.max - this.min > this.maxRange ) {
                        this.min = this.max - this.maxRange;
                        this.setOptions({ xaxis: { min: this.min }});
                    }
                    //console.log('min: ' + this.min);
                }
            });
        }

        // bind the event handler for event `dataSeriesUpdate'
        if(args.onDataSeriesUpdate && 
                typeof args.onDataSeriesUpdate == 'function') {
            jQuery(this).bind('dataSeriesUpdate', args.onDataSeriesUpdate);
        }

        if(args.data) {
            // args.data may be a single DataSeries instance or an array of them
            var dataSeriesList;
            if(args.data instanceof Array) dataSeriesList = args.data;
            else dataSeriesList = [ args.data ];

            for(var i = 0; i < dataSeriesList.length; i++) {
                this.addDataSeries(dataSeriesList[i]);
            }
        }

    },
    methods: {

        addDataSeries: function(dataSeries) {
            this.data[dataSeries.name] = dataSeries;
            this.rawSeries.push(dataSeries.rawSeries);
            jQuery(this).trigger('dataSeriesUpdate', [ dataSeries ]);
        },

        updateDataSeries: function(dataSeriesName, rawdata) {
            this.data[dataSeriesName].appendData(rawdata);
            jQuery(this).trigger('dataSeriesUpdate', [ this.data[dataSeriesName] ]);
        },

        extend: function(original, obj) {
            for(var o in obj) {
                if(typeof original[o] == 'object') 
                    this.extend(original[o], obj[o]);
                else jQuery.extend(original, obj);
            }
        },

        setOptions: function(options) {
            //jQuery.extend(this.options, options);
            this.extend(this.options, options);
        },

        doPlot: function () {
            jQuery.plot(this.canvas, this.rawSeries, this.options);
        },

        setAutoUpdate: function(dataSeries, period, updateFunc, args) {
            if(typeof dataSeries == 'string') 
                dataSeries = this.data[dataSeries];
            dataSeries.autoUpdate = true;
            var update = function() {
                if(dataSeries.autoUpdate) {
                    updateFunc(dataSeries, args);
                    //this.updateDataSeries(dataSeries, updateFunc(args));
                    dataSeries.autoUpdateId = setTimeout(update, period);
                }
            };                    
            return update;
        },

        clearAutoUpdata: function(dataSeries) {
            if(typeof dataSeries == 'string') 
                dataSeries = this.data[dataSeries];
            dataSeries.autoUpdate = false;
            timeoutId = dataSeries.autoUpdateId;
            console.log(timeoutId);
            if(typeof timeoutId == 'number') 
                clearTimeout(timeoutId);
        }
    }
        
});


/**
 * PerfDataSeries
 */
var PerfDataSeries = defineClass({
    borrows: DataSeries,
    construct: function(args) {
        DataSeries.call(this, args);
        this.host = args.host;
        this.metric = args.metric;
        this.unit = args.unit || 'none';
        this.title = args.title || args.metric;
        urlArgs = {
            host: args.host,
            metric: args.metric,
            cf: args.cf
            //step: args.step
        }
        var url = args.urlTemplate;
        //var url;
        //this.urlTemplate = url = args.urlTemplate;
        
        //var tempUrl = url, tempArg = '', s = start = end = 0;
        //for(var i = 0; i < url.length; i++) {
            //if(url.charAt(i) == '{') {
                //s = 1;
                //start = i;
                //continue;
            //} else if(url.charAt(i) == '}') {
                //s = 0;
                //end = i;
                //if(urlArgs[tempArg] !== undefined)
                    //tempUrl = tempUrl.substring(0, start) + 
                                //urlArgs[tempArg] +
                                //tempUrl.substring(end + 1);
                //tempArg = '';
                //continue;
            //}
            //if(s == 1) tempArg += url.charAt(i);
        //}
        //url = tempUrl;
        //console.log(url);
        
        var pattern;
        for(var arg in urlArgs) {
            if(urlArgs[arg] !== undefined) {
                pattern = new RegExp('\{' + arg + '\}');
                url = url.replace(pattern, urlArgs[arg]);
            }
        }
        console.log(url);

        if(url.indexOf('{') != -1) {
            var splits = url.split('?', 2);
            url = splits[0];
            var args = splits[1];
            if(url.indexOf('{') != -1) 
                throw new Error('invalid url');
            argsArr = args.split('&');
            args = '';
            for(var i = 0; i < argsArr.length; i++) {
                if(argsArr[i].indexOf('{') == -1) args += argsArr[i] + '&';
            }
            args = args.slice(0, -1);
            if(args.length) url = url + '?' + args;
        }
        console.log(url);

        this.url = url;
        //TODO: fetch metric title from server
        if(!this.rawSeries.label) this.rawSeries.label = this.title;
    },
    methods: {
        setArg: function(argName, argValue) {
            var i = this.url.indexOf(argName);
            if(i != -1) {
                var url = this.url;
                url = url.substring(0, i + argName.length + 1) +
                            argValue +
                            url.substring(url.indexOf('&', i));
                this.url = url;
            }
        }
    }
});

            
/**
 * PerfChart -- performance chart for monitored resources
 *
 */
var PerfChart = defineClass({
    borrows: PlotWrapper,
    construct: function(args) {
        this.step = args.step;
        var maxRange;
        if(args.maxRange === undefined) {
            if(this.step <= 60) 
                maxRange = 3600;
            else if(this.step <= 600)
                maxRange = 3600 * 24;
            else if(this.step <= 3600)
                maxRange = 3600 * 24 * 3;
            else maxRange = 0;
            //overwrite the args
            args.maxRange = maxRange;
        }

        this.yaxes = {};
        PlotWrapper.call(this, args);
        
        this.setOptions({
            xaxis: {
                tickFormatter: timeFormatter(this.step)
            }
        });

    },
    methods: {
        setRealTime: function(period) {
            var plotter = this;
            for(var dname in this.data) {
                var dataSeries = this.data[dname];
                var start, step, l;
                if(l = dataSeries.rawSeries.data.length) {
                    start = dataSeries.rawSeries.data[l-1][0];
                    if(l > 1) 
                        step = dataSeries.rawSeries.data[1][0] -
                                dataSeries.rawSeries.data[0][0];
                    else step = this.step;
                } else {
                    start = this.maxRange ? -this.maxRange : -this.step * 120,
                    step = this.step
                }
                var updateArgs = {
                    start: start,
                    step: step
                };
                if(dataSeries instanceof PerfDataSeries) {
                    this.setAutoUpdate(dataSeries, period, function(ds, args) {
                        jQuery.get(ds.url,
                            args,
                            function(data) {
                                step = data[0][2];
                                data = data[1];
                                plotter.updateDataSeries(ds.name, data);
                                args.start = data[data.length - 1][0] + step;
                                plotter.doPlot();
                            }, 'json');
                    }, updateArgs)();
                }
            }
        }, 
        unsetRealTime: function(period) {
            for(var dname in this.data) 
                this.clearAutoUpdata(dname);
        },
        addDataSeries: function(dataSeries) {
            if (dataSeries instanceof PerfDataSeries) {
                var unit = dataSeries.unit;
                if (!(unit in this.yaxes)) {
                    var u = {};
                    switch(unit) {
                        case 'pct':
                            u.min = 0, u.max = 100;
                            u.tickDecimals = 0;
                            u.tickFormatter = function(val, axis) {
                                return val.toFixed(axis.tickDecimals) + '%';
                            }
                            break;
                        case 'kB':
                            u.tickDecimals = 1;
                            u.tickFormatter = function(val, axis) {
                                return scaleBytes(val * 1024, axis.tickDecimals, 2, '');
                            }
                            break;
                        case 'kB/s':
                            u.tickDecimals = 1;
                            u.tickFormatter = function(val, axis) {
                                return scaleBytes(val * 1024, axis.tickDecimals, 2, '/s');
                            }
                            break;
                        case 'B/s':
                            u.tickDecimals = 1;
                            u.tickFormatter = function(val, axis) {
                                return scaleBytes(val, axis.tickDecimals, 10, '/s');
                            }
                            break;
                        default:
                            break;
                    }
                    var oldYaxes = this.options.yaxes || [];
                    var index = oldYaxes.length + 1;
                    if (index % 2 == 0) {
                        u.position = 'right';
                        u.alignTicksWithAxis = 1;
                    }
                    this.setOptions({
                        yaxes: oldYaxes.concat(u)
                    });
                    this.yaxes[unit] = index;
                }
                dataSeries.rawSeries.yaxis = this.yaxes[unit];
            }
            PlotWrapper.prototype.addDataSeries.call(this, dataSeries);
        },
    } 
});
