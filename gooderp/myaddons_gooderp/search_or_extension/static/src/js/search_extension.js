odoo.define('jifixup.main', function (require) {
    "use strict";
    var core = require('web.core');
    var search_field = require('web.search_inputs').Field;
    var many2one = core.search_widgets_registry.get('many2one');
    var QWeb = core.qweb;
    var _lt = core._lt;

    search_field.include({
        make_domain: function (name, operator, facet) {
            var domains = [];
            _.each(this.value_from(facet).split(";"), function (e) {
                domains.push([name, operator, e])
            });
            var mlen = domains.length - 1;
            for(var i =0; i < mlen; i++) {
                domains.unshift("|");
            }
            return domains;
        }
    });
    many2one.include({
        make_domain: function (name, operator, facetValue) {
            operator = facetValue.get('operator') || operator;

            if (operator == this.default_operator) {
                operator = '=';
            }

            var domains = [];
            _.each(facetValue.get('value').split(";"), function (e) {
                domains.push([name, operator, e])
            });
            var mlen = domains.length - 1;
            for(var i =0; i < mlen; i++) {
                domains.unshift("|");
            }

            return domains;
        }
    })
});