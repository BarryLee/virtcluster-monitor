/*
* Requires PlotWrapper.js
*/


/**
 * PerfDataSeries
 */
var PerfDataSeries = defineClass({
    borrows: DataSeries,
    construct: function(args) {
        if (args.cf === undefined)
            args.cf = 'AVERAGE';
        if (args.name === undefined) 
            args.name = args.host + '.' + args.metric + '.' + args.cf;
        DataSeries.call(this, args);
        this.host = args.host;
        this.metric = args.metric;
        this.unit = args.unit || 'none';
        this.title = args.title || args.metric;
        this.cf = args.cf;
        this.step = args.step || 1;
        urlArgs = {
            host: this.host,
            metric: this.metric,
            cf: this.cf,
            step: this.step
        }
        
        /*
        * another method to form url (probably works)
        var url;
        this.urlTemplate = url = args.urlTemplate;
        
        var tempUrl = url, tempArg = '', s = start = end = 0;
        for(var i = 0; i < url.length; i++) {
            if(url.charAt(i) == '{') {
                s = 1;
                start = i;
                continue;
            } else if(url.charAt(i) == '}') {
                s = 0;
                end = i;
                if(urlArgs[tempArg] !== undefined)
                    tempUrl = tempUrl.substring(0, start) + 
                                urlArgs[tempArg] +
                                tempUrl.substring(end + 1);
                tempArg = '';
                continue;
            }
            if(s == 1) tempArg += url.charAt(i);
        }
        url = tempUrl;
        console.log(url);
        */
        
        var url = args.urlTemplate;
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
        setUrlArg: function(argName, argValue) {
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
        if(args.maxRange === undefined) {
            var maxRange;
            if(this.step <= 60) 
                maxRange = 3600;
            else if(this.step <= 600)
                maxRange = 3600 * 24;
            else if(this.step <= 3600)
                maxRange = 3600 * 24 * 3;
            else maxRange = 0;
            // overwrite the args
            args.maxRange = maxRange;
        }

        this.yaxes = {};
        PlotWrapper.call(this, args);
        
        this.setOptions({
            xaxis: {
                tickFormatter: timeFormatter(this.step)
            }
        });

        if (args.metrics) {
            for (var i = 0; i < args.metrics.length; i++) {
                this.addMetric(args.metrics[i]);                
            }
        }
    },
    methods: {
        setRealTime: function(period) {
            var plotter = this;
            // set auto update for all metrics
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
                    step: step,
                    cf: dataSeries.cf
                };
                if(dataSeries instanceof PerfDataSeries) {
                    this.setAutoUpdate(dataSeries, period, function(ds, args) {
                        jQuery.get(ds.url,
                            args,
                            function(data) {
                                //step = data[0][2];
                                //data = data[1];
                                if (data.length) {
                                    plotter.updateDataSeries(ds.name, data);
                                    args.start = data[data.length - 1][0] + step;
                                    plotter.doPlot();
                                }
                            }, 'json');
                    }, updateArgs)();
                } // end if
            } // end for
            return this;
        }, 

        unsetRealTime: function(period) {
            for(var dname in this.data) 
                this.clearAutoUpdata(dname);
            return this;
        },

        _addUnitAxis: function(unit) {
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
        },

        addDataSeries: function(dataSeries) {
            if (dataSeries instanceof PerfDataSeries) {
                var unit = dataSeries.unit;
                if (!(unit in this.yaxes)) {
                    this._addUnitAxis(unit);
                }
                dataSeries.rawSeries.yaxis = this.yaxes[unit];
            }
            PlotWrapper.prototype.addDataSeries.call(this, dataSeries);
            return this;
        },

        addMetric: function(metricAttr) {
            var dataSeries = new PerfDataSeries(metricAttr);
            return this.addDataSeries(dataSeries);
        },

        plotOnce: function() {
            jQuery(this).one('dataSeriesUpdate', function() { 
                this.unsetRealTime();
            });
            this.setRealTime(60000);
            return this;
        }
    } 
});
