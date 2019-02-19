openerp.sh_common_preview_image = function (instance) {
    instance.web.form.FieldBinaryImage.include({
        render_value: function() {
            this._super();
            var self = this;
            $img = this.$el.find('> img');
            $img.on('mouseover', function(e) {
                $preview = $('.mypreviewimage');
                if ($preview.length == 0) {
                    $preview = $("<div class='mypreviewimage'><img style='width:500px;height:500px'/></div>")
                    $preview.appendTo($("body"));
                }
                $preview.css("left", $img.offset().left + $img.outerWidth() + 5 + "px");
                $preview.css("top", $img.offset().top + "px");
                $preview.css("display", "block").css("position", "absolute").css("z-index", 10000).css("background", "white").css("border", "solid 1px green");
                var id = JSON.stringify(self.view.datarecord.id || null);
                var url = self.session.url('/web/binary/image', {
                                        model: self.view.dataset.model,
                                        id: id,
                                        field: 'image',
                                        t: (new Date().getTime()),
                            });
                $preview.find("img").attr("src", url);
                $preview.show();
            });
            $img.on('mouseout', function (e)  {
                $preview = $('.mypreviewimage');
                $preview.hide();
            });
        }
    });
}