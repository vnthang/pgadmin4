define(
    ['underscore', 'pgadmin', 'wcdocker'],
function(_, pgAdmin) {

  var pgBrowser = pgAdmin.Browser = pgAdmin.Browser || {};

  pgAdmin.Browser.Panel = function(options) {
    var defaults = [
      'name', 'title', 'width', 'height', 'showTitle', 'isCloseable',
      'isPrivate', 'content', 'icon', 'events', 'onCreate'];
    _.extend(this, _.pick(options, defaults));
  }

  _.extend(pgAdmin.Browser.Panel.prototype, {
    name:'',
    title: '',
    width: 300,
    height: 600,
    showTitle: true,
    isCloseable: true,
    isPrivate: false,
    content: '',
    icon: '',
    panel: null,
    onCreate: null,
    load: function(docker, title) {
      var that = this;
      if (!that.panel) {
        docker.registerPanelType(that.name, {
          title: that.title,
          isPrivate: that.isPrivate,
          onCreate: function(myPanel) {
            $(myPanel).data('pgAdminName', that.name);
            myPanel.initSize(that.width, that.height);

            if (!that.showTitle)
              myPanel.title(false);
            else {
              myPanel.title(title || that.title);
              if (that.icon != '')
                myPanel.icon(that.icon)
            }

            var $container = $('<div>', {
              'class': 'pg-panel-content'
            }).append($(that.content));

            myPanel.closeable(!!that.isCloseable);
            myPanel.layout().addItem($container);
            that.panel = myPanel;
            if (that.events && _.isObject(that.events)) {
              _.each(that.events, function(v, k) {
                if (v && _.isFunction(v)) {
                  myPanel.on(k, v);
                }
              });
            }
            _.each([
                wcDocker.EVENT.UPDATED, wcDocker.EVENT.VISIBILITY_CHANGED,
                wcDocker.EVENT.BEGIN_DOCK, wcDocker.EVENT.END_DOCK,
                wcDocker.EVENT.GAIN_FOCUS, wcDocker.EVENT.LOST_FOCUS,
                wcDocker.EVENT.CLOSED, wcDocker.EVENT.BUTTON,
                wcDocker.EVENT.ATTACHED, wcDocker.EVENT.DETACHED,
                wcDocker.EVENT.MOVE_STARTED, wcDocker.EVENT.MOVE_ENDED,
                wcDocker.EVENT.MOVED, wcDocker.EVENT.RESIZE_STARTED,
                wcDocker.EVENT.RESIZE_ENDED, wcDocker.EVENT.RESIZED,
                wcDocker.EVENT.SCROLLED], function(ev) {
                  myPanel.on(ev, that.eventFunc.bind(myPanel, ev));
                });

            if (that.onCreate && _.isFunction(that.onCreate)) {
              that.onCreate.apply(that, [myPanel, $container]);
            }
          }
        });
      }
    },
    eventFunc: function(eventName) {
      var name = $(this).data('pgAdminName');

      try {
        pgBrowser.Events.trigger('pgadmin-browser:panel', eventName, this, arguments);
        pgBrowser.Events.trigger('pgadmin-browser:panel:' + eventName, this, arguments);

        if (name) {
          pgBrowser.Events.trigger('pgadmin-browser:panel-' + name, eventName, this, arguments);
          pgBrowser.Events.trigger('pgadmin-browser:panel-' + name + ':' + eventName, this, arguments);
        }
      } catch (e) {
        console.log(e);
      }
    }
  });

  return pgAdmin.Browser.Panel;
});
