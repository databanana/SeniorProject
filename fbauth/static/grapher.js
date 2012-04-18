//color scheme: http://colorschemedesigner.com/#3i31Tw0w0w0w0
$(document).ready(function() {
    var pwidth = $("#papercontainer").width();
    var pheight =  $("#papercontainer").height();
    var paper = new Raphael($("#papercontainer")[0], pwidth, pheight);
    console.log("height:" + pheight);

    //Set up variables

    var fadeInDuration = 1500;
    
    var nodeAttr = {
        stroke: "#000000",
        'stroke-width': 3,
        //'r': 10,
    };

    var nodeColor = "#ff7373";
    
    var nodeRadius = 6;

    var nodeHoverAttr = {
        'stroke-width': nodeRadius*1.5/6,
        //'r': 10,
    };

    
    var edgeAttr = {
        stroke: "#33CCCC",
        'stroke-width': 0.5,
    };
    
    var edgeHoverAttr = {
        'stroke-width': 1,
    };

    var nameattr = {
        'fill': '#999999',
        'opacity': 0.6,
    }

    //Set up overlays
    $("#overlay").width(pwidth);
    $("#overlay").height(pheight);
    $("#overlay").position({'of': $("#papercontainer")});

    $(".loadingindicator").position({'of': $("#overlay"), 'collision': 'none'});

    //$("#loadingbarwrapper").position({'of': $("#overlay")});
    $("#loadingbar").progressbar();

    //Hide overlays
    $(".loadingindicator").hide();
    $("#overlay").hide();

    //Set up buttons
    $("input:button").button();


    //Set up controls


  $("h3 + div").each(function() {$(this).prev().andSelf().wrapAll("<div class='controlwrapper' />")});
  $(".controlwrapper").addClass('ui-helper-reset ui-corner-all ui-widget');

  $(".controltoggle").addClass('ui-helper-reset ui-widget');
  $(".controlwrapper > h3").addClass('ui-helper-reset ui-widget-header ui-state-default ui-state-active');
  $(".controlwrapper > div").addClass('ui-helper-reset ui-widget-content');
  $(".controlwrapper > div").css('border','none');
  $(".controlwrapper > h3").css('border','none');

  $(".controlwrapper > h3").wrapInner("<span class='controlboxittle' />");
  $(".controlwrapper > h3 > span").prepend("<span class='ui-icon  ui-icon-triangle-1-e ui-icon-triangle-1-s' />");

  $(".controlwrapper > h3").click(function() {
    $(this).next().toggle({'effect':'blind'}, repositionElements);
    $(this).toggleClass('ui-state-active');
    $(this).contents().contents().first().toggleClass('ui-icon-triangle-1-s');
  });


  //Graph Options
  //Layout
  $("#currentlayout").button()
    .next()
    .button({
      'text':false,
      'icons': {
        'primary':'ui-icon-triangle-1-s',
      }
    })
    .parent()
      .buttonset();

  $("#selectlayout").click(function() {
    $("#layoutlist").toggle('blind');
  });


  $("#layoutlist").addClass('ui-helper-clear ui-autocomplete ui-menu ui-widget ui-widget-content ui-corner-all');
  $("#layoutlist li").addClass("ui-helper-clear ui-menu-item ui-corner-all");
  $("#layoutlist li").hover(function() {$(this).toggleClass('ui-state-hover');});
  $("#layoutlist").selectable({'stop': function() {
      if (grapher.loadedNodes) {
        $("#overlay").show();
        $("#loadingcircle").show();
        $(".loadingtext").text("Loading friend positions...");
      }
      var selection = $("#layoutlist .ui-selected").text();
      $("#currentlayout").text(selection);
      $("#layoutlist").toggle('blind');
      if (selection=="Radial") {
        grapher.engine = "twopi";
        if (!grapher.loadedNodes) return;
        Dajaxice.fbauth.position_friends(Dajax.process, {
            'engine': 'twopi',
            'width': $('#papercontainer').width(),
            'height':$('#papercontainer').height(),
            'widthoffset':$('#controls').width(),
        });
      } else if (selection=="Force-directed") {
        grapher.engine = "sfdp";
        if (!grapher.loadedNodes) return;
        Dajaxice.fbauth.position_friends(Dajax.process, {
            'engine': 'sfdp',
            'width': $('#papercontainer').width(),
            'height':$('#papercontainer').height(),
            'widthoffset':$('#controls').width(),
        });
      }
    }
  });

  //Edge width

  $("#linewidthselector").slider({'min':0.1,
    'max': 4,
    'step':0.1,
    'value': edgeAttr['stroke-width'],
    'slide': function(event, ui) {
        $("#linewidth").val(ui.value);
    },
    'stop':function(event, ui) {
        grapher.setLineWidth(ui.value);
    },
  });

  $("#linewidth").val(edgeAttr['stroke-width']);

  //Node radius

  $("#nodesizeselector").slider({'min':1, 'max':50, 'value':nodeRadius, slide: function(event, ui) {
        $("#nodesize").val(ui.value);
    },
    'stop': function(event, ui) {
        grapher.setCircleRadius(ui.value);
        $("#currentranker").text("Disabled");
        $("#sizerangeselector").slider('disable');   
    }
  });

  $("#nodesize").val(nodeRadius);

  //Color selectors
  var colorparts = ['00','55','AA','FF'];
  for (var i in colorparts) {
    for (var j in colorparts) {
        for (var k in colorparts) {
            var c = colorparts[i] + colorparts[j] + colorparts[k];
            $(".colorselector").append("<option value='"+c+"'>#" + c + "</option>");
        }
    }
  }

  $(".colorselector").colourPicker({'ico':window.static_url+'jquery.colourPicker.gif', 'title':false});

  $("[name='nodecolor']").val(nodeColor.substring(1)).css('background', nodeColor);
  $("[name='edgecolor']").val(edgeAttr['stroke'].substring(1)).css('background', edgeAttr['stroke']);


  $("[name='nodecolor']").change(function() {
    $("#clusteringOff").checked = true;
    nodeColor = '#' + $("[name='nodecolor']").val();
    grapher.updateAllNodeColors();
  });
  $("[name='edgecolor']").change(function() {
    edgeAttr['stroke'] = '#' + $("[name='edgecolor']").val();
    grapher.updateAllEdgeAttr();
  });

  //Analysis
  //Community clustering

  $("[name='communityCluster']").button().button('disable');
  //$("#clusteringRadio").buttonset();
  $("[name='communityCluster']").click(function() {
    $("[name='nodecolor']").val("--");
    grapher.findCommunities(1);
  });

  //Cenrality ranking
  $("#currentranker").button()
    .next()
    .button({
      'text':false,
      'icons': {
        'primary':'ui-icon-triangle-1-s',
      }
    })
    .parent()
      .buttonset();

  $("#currentranker").button('disable');
  
  $("#selectranker").click(function() {
    $("#ranklist").toggle('blind');
  }).button('disable');

  $("#ranklist").addClass('ui-helper-clear ui-autocomplete ui-menu ui-widget ui-widget-content ui-corner-all');
  $("#ranklist li").addClass("ui-helper-clear ui-menu-item ui-corner-all");
  $("#ranklist li").hover(function() {$(this).toggleClass('ui-state-hover');});
  $("#ranklist").selectable({'stop': function() {
        var selection = $("#ranklist .ui-selected").text();
        if (selection=="Disabled") {
            $("#sizerangeselector").slider('disable');
        } else {
            $("#nodesize").val('--');
            $("#sizerangeselector").slider('enable');
            var minradius = $("#sizerangeselector").slider('values')[0];
            var maxradius = $("#sizerangeselector").slider('values')[1];
            $("#overlay").show();
            $("#loadingcircle").show();
            $("#loadingtext").text('Calculating ranks...');
            Dajaxice.fbauth.get_rank(Dajax.process,{'algorithm':selection, 'min_radius':minradius, 'max_radius':maxradius});
      }
      $("#currentranker").text(selection);
      $("#ranklist").toggle('blind');

        //Resize stuff
    }
  });


  //Size range
  $("#minradius").val(0);
  $("#maxradius").val(50);
  $("#sizerangeselector").slider({
    'range': true,
    'min':1,
    'max': 50,
    'step': 1,
    'values': [1, 50],
    'stop':function(event, ui) {
        $("#nodesize").val('--');
        $("#minradius").val(ui.values[0]);
        $("#maxradius").val(ui.values[1]);
        $("#overlay").show();
        $("#loadingcircle").show();
        $("#loadingtext").text('Calculating ranks...');
        var engine = $("#currentranker").text();
        Dajaxice.fbauth.get_rank(Dajax.process,{'algorithm':engine, min_radius:ui.values[0], max_radius:ui.values[1]});
    },
  }).slider('disable');

  //Position and hide elements

  repositionElements = function() {
    $(".dropdownlist").show();
    $("#ranklist").position({'of':$("#currentranker"), 'at':'left bottom', 'my':'left top'});
    $("#layoutlist").position({'of':$("#currentlayout"), 'at':'left bottom', 'my':'left top'});
    $(".dropdownlist").hide();
  }

  repositionElements();

  $("#layoutlist").width($("#currentlayout").width());
  $("#ranklist").width($("#currentlayout").width());

  $(".controlwrapper > h3").each(function() {
    $(this).next().hide();
    $(this).toggleClass('ui-state-active');
    $(this).contents().contents().first().toggleClass('ui-icon-triangle-1-s');
  });

  //Open first control box
  var firstbox = $(".controlwrapper > h3").first();
  firstbox.toggleClass('ui-state-active').contents().contents().first().toggleClass('ui-icon-triangle-1-s');
  firstbox.next().show();


    //Set up graph objects

    var Node = function(id, name, x, y, r) {
        this.name = name;
        this.id = id;
        this.x = x;
        this.y = y;
        this.dx = 0;
        this.dy = 0;
        this.r = r;
        this.edges = [];
        this.edgesIn = [];
        this.edgesOut = [];
        this.moving = false;
        this.mouseover = false;
        this.displaytext = null;
        this.displaybox = null;
        this.rankVal = null;
        this.addEdge = function(endNode) {
            var e  = new Edge(this, endNode);
            this.edgesOut[this.edgesOut.length] = e;
            endNode.edgesIn[endNode.edgesIn.length] = e;
            return e;
        };
        this.circle = paper.circle(this.x, this.y, this.r);
        this.circle.attr('opacity', 0);
        this.circle.attr(nodeAttr);
        this.circle.attr('r', nodeRadius);
        this.circle.attr('stroke-width', nodeRadius/6);
        this.circle.attr('fill', nodeColor);
        this.circle.animate({'opacity':1}, fadeInDuration, '>');
        this.move = function(dx, dy) {
            this.dx = dx;
            this.dy = dy;
            this.circle.attr('cx', this.x + this.dx);
            this.circle.attr('cy', this.y + this.dy);
            for (var i in this.edgesOut) {
                this.edgesOut[i].drawLine();
            }
            for (var i in this.edgesIn) {
                this.edgesIn[i].drawLine();
            }
        };
        this.position = function(x, y) {
            this.dx = 0;
            this.dy = 0;
            this.x = x;
            this.y = y;
            this.circle.animate({'cx': this.x, 'cy': this.y}, 1500, '<>');
            //this.circle.attr('cx', this.x);
            //this.circle.attr('cy', this.y);
        }
        this.startMove = function() {
            this.hideName();
            this.moving = true;
            this.circle.toFront();
            this.x = this.x + this.dx;
            this.y = this.y + this.dy;
            this.dy = 0;
            this.dx = 0;
        }
        this.endMove = function() {
            this.moving = false;
            this.x = this.x + this.dx;
            this.y = this.y + this.dy;
            this.dy = 0;
            this.dx = 0;
            if (this.mouseover) this.drawName();
        }
        this.mouseEnter = function() {
            //this.circle.attr(nodeHoverAttr);
            this.mouseover = true;
            this.highlight();
            for (var i in this.edgesIn) {
                this.edgesIn[i].highlight();
                this.edgesIn[i].startNode.highlight();
            };
            for (var i in this.edgesOut) {
                this.edgesOut[i].highlight();
                this.edgesOut[i].endNode.highlight();
            }
            this.circle.toFront();
        }
        this.mouseExit = function() {
            //this.circle.attr(nodeAttr);
            this.mouseover = false;
            if (!this.moving) this.unhighlight();
            for (var i in this.edgesIn) {
                this.edgesIn[i].unhighlight();
                this.edgesIn[i].startNode.unhighlight();
            };
            for (var i in this.edgesOut) {
                this.edgesOut[i].unhighlight();
                this.edgesOut[i].endNode.unhighlight();
            }
        }
        this.highlight = function() {
            //this.circle.toFront();
            if (this.moving == false) this.drawName();
            this.circle.animate({'stroke-width':this.circle.attr('r') * 1.5/6}, 100, '>');
        }
        this.unhighlight = function() {
            this.hideName();
            this.circle.animate({'stroke-width':this.circle.attr('r')/6}, 100, '>');
        }
        this.drawName = function () {
            if (this.displaytext != null) this.displaytext.remove();
            if (this.displaybox != null) this.displaybox.remove();
            this.displaytext = paper.text(this.x, this.y-20, this.name);
            var bbox = this.displaytext.getBBox();
            this.displaybox = paper.rect(bbox['x']-3, bbox['y']-3, bbox['width']+6, bbox['height']+6, 3);
            this.displaybox.attr(nameattr);
            this.displaybox.toFront();
            this.displaytext.toFront();
        }
        this.hideName = function() {
            if (this.displaytext != null) this.displaytext.remove();
            if (this.displaybox != null) this.displaybox.remove();
        }
        this.circle.drag(this.move, this.startMove, this.endMove, this, this);
        this.circle.hover(this.mouseEnter, this.mouseExit, this, this);
    }

    
    var Edge = function(startNode, endNode) {
        this.startNode = startNode;
        this.endNode = endNode;
        this.drawLine = function() {
            this.line.attr('path', "M"+(this.startNode.x+this.startNode.dx)+" "+(this.startNode.y+this.startNode.dy)+"L"+(this.endNode.x + this.endNode.dx) +" "+ (this.endNode.y+this.endNode.dy));
        };
        this.highlight = function() {
            //this.line.attr(edgeHoverAttr);
            this.line.animate(edgeHoverAttr,100, '>');
        }
        this.unhighlight = function() {
            //this.line.attr(edgeAttr);
            this.line.animate(edgeAttr,100,'>');
        }
        this.line = paper.path();
        this.line.toBack();
        this.line.attr('opacity', 0);
        this.line.attr(edgeAttr);
        this.drawLine();
        this.reveal = function () {
            this.line.animate({'opacity':1}, fadeInDuration, '>');
        }
        this.hide = function() {
            this.line.animate({'opacity':0}, fadeInDuration, '>');
        }
    }


    //Graph object and functions

    window.grapher = {};

    grapher.loadedNodes = false;
    grapher.loadedEdges = false;

    grapher.graph = {};

    grapher.edges = [];

    grapher.engine = "sfdp";

    var graph = grapher.graph;  

    grapher.add_nodes = function(node_names) {
        $("#currentranker").button('enable');
        $("#selectranker").button('enable');
        $("[name='communityCluster']").button('enable');
        grapher.loadedNodes = true;
        //console.log(node_ids);
        $(".loadingtext").text("Drawing friends...");
        var controlsWidth = $("#controls").width();
        for (id in node_names) {
            graph[id] = new Node(id, node_names[id], Math.floor(Math.random()*(pwidth-20-controlsWidth)+10+controlsWidth), Math.floor(Math.random()*(pheight-20))+10, 10);
        }
        $("#loadingcircle").hide();
        $("#overlay").hide();
    }

    grapher.set_positions = function(node_positions) {
        grapher.hideAllEdges();
        $("#overlay").show();
        $("#loadingcircle").show();
        $(".loadingtext").text("Positioning friends...");
        for (id in node_positions) {
            //console.log(graph[id]);
            if (id in graph) graph[id].position(node_positions[id][0], node_positions[id][1]);
            else console.log(id);
        }
        grapher.positionAllEdges();
        grapher.revealAllEdges();
        $("#loadingcircle").hide();
        $("#overlay").hide();
    }

    grapher.add_edges = function(edges) {
        grapher.loadedEdges = true;
        $("#loadingcircle").hide();
        $("#loadingbarwrapper").show();
        $(".loadingtext").text("Drawing connections...");
        var timeout = 50;
        var chunk_limit = 300;
        var chunk_counter = 0;
        var i = 0;
        var add = function() {
                for (; i < edges.length; i++) {
                    if (!(edges[i][0] in graph) || !(edges[i][1] in graph)) continue;
                    var node1 = graph[edges[i][0]];
                    var node2 = graph[edges[i][1]];
                    var e = node1.addEdge(node2);
                    grapher.edges[grapher.edges.length] = e;
                    chunk_counter++;
                    if (chunk_counter >= chunk_limit) {
                        $("#loadingbar").progressbar({'value':i/edges.length * 100});
                        chunk_counter = 0;
                        console.log("added chunk")
                        setTimeout(add, timeout);
                        break;
                    }
                }
                if (i == edges.length) {
                    $("#loadingbarwrapper").hide();
                    $("#loadingcircle").show();
                    grapher.revealAllEdges();
                    $("#loadingcircle").hide();
                    $("#overlay").hide();
                }
        }
        add();
    }

    grapher.auto_load = function() {
        $('#overlay').show();
        $('#loadingcircle').show();
        $('.loadingtext').text('Loading friends...');
        if (!grapher.loadedNodes) {
            //Load nodes, then continue
            Dajaxice.fbauth.get_friend_ids(Dajax.process, {
                'auto':true,
            });
        } else if(!grapher.loadedEdges) {
            //Position friends, then continue
            Dajaxice.fbauth.position_friends(Dajax.process, {
                'engine': grapher.engine,
                'width': $('#papercontainer').width(),
                'height':$('#papercontainer').height(),
                'widthoffset':$('#controls').width(),
                'auto':true,
            });
        } else {
            //Just position friends
            Dajaxice.fbauth.position_friends(Dajax.process, {
                'engine': grapher.engine,
                'width': $('#papercontainer').width(),
                'height':$('#papercontainer').height(),
                'widthoffset':$('#controls').width(),
            }); 
        }
    }

    grapher.auto_add_nodes = function (node_names) {
        grapher.add_nodes(node_names);
        $('#overlay').show();
        $('#loadingcircle').show();
        $('.loadingtext').text('Calculating layout...');
        Dajaxice.fbauth.position_friends(Dajax.process, {
            'engine': grapher.engine,
            'width': $('#papercontainer').width(),
            'height':$('#papercontainer').height(),
            'widthoffset':$('#controls').width(),
            'auto':true,
        });
    }

    grapher.auto_set_positions = function(node_positions) {
        grapher.set_positions(node_positions);
        $('#overlay').show();
        $('#loadingcircle').show();
        $('.loadingtext').text('Loading connections...');
        Dajaxice.fbauth.connect_friends(Dajax.process);
    }

    grapher.revealAllEdges = function() {
        for(i in grapher.edges) {
            grapher.edges[i].reveal();
        }
    }

    grapher.hideAllEdges = function() {
        for (i in grapher.edges) {
            grapher.edges[i].hide();
        }
    }

    grapher.positionAllEdges = function() {
        for (i in grapher.edges) {
            grapher.edges[i].drawLine();
        }
    }

    grapher.setLineWidth = function(w) {
        edgeAttr['stroke-width'] = w;
        edgeHoverAttr['stroke-width'] = Math.ceil(w*1.5);
        grapher.updateAllEdgeAttr();
    }

    grapher.updateAllEdgeAttr = function () {
        for (i in grapher.edges) {
            grapher.edges[i].line.attr(edgeAttr);
        }
    }

    grapher.updateAllNodeAttr = function() {
        for (i in grapher.graph) {
            grapher.graph[i].circle.attr(nodeAttr);
        }
    }

    grapher.updateAllNodeColors = function() {
        for (i in grapher.graph) {
            grapher.graph[i].circle.attr('fill', nodeColor);
        }
    }

    grapher.setCircleRadius = function(r) {
        nodeStrokeWidth = r/6;
        nodeRadius = r;
        //nodeHoverAttr['stroke-width'] = r*1.5/6;
        console.log("Set stroke width to " + (r/6));
        for (i in grapher.graph) {
            grapher.graph[i].circle.attr({'stroke-width':nodeStrokeWidth, 'r':nodeRadius});
        }
    }

    grapher.waitToPosition = function(args) {
        var djangoargs = {
            'engine': grapher.engine,
            'width': $('#papercontainer').width(),
            'height':$('#papercontainer').height(),
            'widthoffset':$('#controls').width(),
        };
        if (args['auto']) {
            djangoargs['auto'] = true;
        }

        setTimeout(function() {
            Dajaxice.fbauth.position_friends(Dajax.process, djangoargs);
        }, args['time']);
    }

    grapher.findCommunities = function(percentage) {
        $('#overlay').show();
        $('#loadingcircle').show();
        $('.loadingtext').text('Finding communities...');
        Dajaxice.fbauth.find_groups(Dajax.process,{n:percentage});
    }

    grapher.colorGroups = function(colors) {
        console.log(colors);
        $.each(colors, function(index, value) {
            var color = value[0];
            var nodes = value[1];
            for (var i = 0; i < nodes.length; i++) {
                grapher.graph[nodes[i]].circle.attr('fill', color);
            }
        });
        $("#overlay").hide();
        $("#loadingcircle").hide();
    }

    grapher.resizeNodes = function(ranks) {
        $.each(ranks, function(node,radius) {
            grapher.graph[node].circle.attr({'r':radius, 'stroke-width':radius/6});
        });
        $("#overlay").hide();
        $("#loadingcircle").hide();
    }
 
});