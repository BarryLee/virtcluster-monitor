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
            return this;
        },
        clearData: function() {
            this.rawSeries.data = [];
            return this;
        }
    }
});


/**
 * PlotWrapper: A Class wraps flot api to enable drawing multiple series in 
 * one chart additively.
 *
 * An example of object argument:
 * { placeholder: '#placeholder', // a jquery object or a selector
 *   data: [ds1, new DataSource('line2')],
 *   onDataSeriesUpdate: function(event) {} }
 */
var PlotWrapper = defineClass({
    construct: function(args) {
        this.canvas = (typeof(args) == 'string') ? jQuery(args): 
            ((typeof(args.placeholder) == 'string') ? jQuery(args.placeholder) :
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
            return this;
        },

        removeDataSeries: function(dataSeriesName) {
            if (dataSeriesName) {
                delete this.data[dataSeriesName];
            } else {
                this.data = {};
            }
            return this;
        },

        updateDataSeries: function(dataSeriesName, rawdata) {
            this.data[dataSeriesName].appendData(rawdata);
            jQuery(this).trigger('dataSeriesUpdate', [ this.data[dataSeriesName] ]);
            return this;
        },

        clearDataSeries: function(dataSeriesName) {
            if (dataSeriesName == null) {
                for (var dsn in this.data)
                    this.data[dsn].clearData();
            } else {
                this.data[dataSeriesName].clearData();
            }
            return this;
        },

        extend: function(original, obj) {
            for(var o in obj) {
                if(typeof original[o] == 'object') 
                    this.extend(original[o], obj[o]);
                else jQuery.extend(original, obj);
            }
            return this;
        },

        setOptions: function(options) {
            //jQuery.extend(this.options, options);
            return this.extend(this.options, options);
        },

        doPlot: function () {
            jQuery.plot(this.canvas, this.rawSeries, this.options);
            return this;
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
            return this;
        }
    }
        
});

