//color scheme: http://colorschemedesigner.com/#3i31Tw0w0w0w0
window.onload = function() {
    //$("#papercontainer").width($(window).width());
    //$("#papercontainer").height($(window).height());
    //$("#papercontainer").width(2000);
    //$("#papercontainer").height(2000);
    var pwidth = $("#papercontainer").width();
    //var pheight = $("#papercontainer").height();
    var pheight =  $("#papercontainer").height();
    //var paper = new Raphael(0,0, $(window).width(), $(window).height());    
    var paper = new Raphael($("#papercontainer")[0], pwidth, pheight);
    console.log("height:" + pheight);

    //Set up overlays
    $("#overlay").width(pwidth);
    $("#overlay").height(pheight);
    $("#overlay").position({'of': $("#papercontainer")});

    $("#loadingcircle").position({'of': $("#overlay")});

    $("#loadingbar").position({'of': $("#overlay")});
    $("#loadingbar").progressbar();

    //Hide overlays
    $("#loadingbar").hide();
    $("#loadingcircle").hide();
    $("#overlay").hide();

    //Set up buttons
    $("input:button").button();

    $('#controltoggle h3').click(function() {$(this).next().toggle('blind');$(this).toggleClass('ui-corner-bottom'); return false; }).next().hide();
    $('#controltoggle h3').wrapInner('<a href="#" />');
    $('#controltoggle h3').prepend('<span></span>');
    $('#controltoggle h3 span').addClass('ui-icon ui-icon-triangle-1-e');
    $("#controltoggle").addClass('ui-helper-reset ui-widget');
    $("#controltoggle h3").addClass('ui-helper-reset ui-widget-header ui-state-default ui-corner-top ui-corner-bottom');
    $("#controltoggle div").addClass('ui-helper-reset ui-widget-content ui-corner-bottom');

    var fadeInDuration = 1500;
    
    var nodeAttr = {
        fill: "#ff7373",
        stroke: "#ff4040",
        'stroke-width': 3,
    };
    
    var nodeHoverAttr = {
        //fill: "#ff7373",
        //stroke: "#ff0000",
        'stroke-width': 5,
    };
    
    var edgeAttr = {
        stroke: "#33CCCC",
        'stroke-width': 3,
    };
    
    var edgeHoverAttr = {
        //stroke: "#009999",
        'stroke-width': 5,
        //opacity: 1,
    };

    var nameattr = {
        'fill': '#999999',
        'opacity': 0.6,
    }

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
        this.addEdge = function(endNode) {
            var e  = new Edge(this, endNode);
            //this.edges[this.edges.length] = e;
            this.edgesOut[this.edgesOut.length] = e;
            endNode.edgesIn[endNode.edgesIn.length] = e;
            return e;
        };
        this.circle = paper.circle(this.x, this.y, this.r);
        this.circle.attr('opacity', 0);
        this.circle.attr(nodeAttr);
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
            this.circle.toFront();
            if (this.moving == false) this.drawName();
            this.circle.animate(nodeHoverAttr, 100, '>');
        }
        this.unhighlight = function() {
            this.hideName();
            this.circle.animate(nodeAttr, 100, '>');
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



    window.grapher = {};

    grapher.graph = {};  

    var graph = grapher.graph;  

    grapher.add_nodes = function(node_names) {
        //console.log(node_ids);
        for (id in node_names) {
            graph[id] = new Node(id, node_names[id], Math.floor(Math.random()*(pwidth-20))+10, Math.floor(Math.random()*(pheight-20))+10, 10);
        }
        $("#loadingcircle").hide();
        $("#overlay").hide();
    }

    grapher.set_positions = function(node_positions) {
        for (id in node_positions) {
            //console.log(graph[id]);
            graph[id].position(node_positions[id][0], node_positions[id][1]);
        }
        $("#loadingcircle").hide();
        $("#overlay").hide();
    }

    grapher.edges = [];

    grapher.add_edges = function(edges) {
        $("#loadingcircle").hide();
        $("#loadingbar").show();
        var timeout = 50;
        var chunk_limit = 300;
        var chunk_counter = 0;
        var i = 0;
        var add = function() {
                for (; i < edges.length; i++) {
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
                    $("#loadingbar").hide();
                    $("#loadingcircle").show();
                    grapher.revealAllEdges();
                    $("#loadingcircle").hide();
                    $("#overlay").hide();
                }
        }
        add();
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
    
    var plotGraph = function(layout) {
        for (name in layout) {
            graph[name] = new Node(layout[name][0], layout[name][1], 20);
        }
    }
    
    window.plotLinks = function(links) {
        //var l = new LoadingBar("Loading...");
        for (var i = 0; i<links.length; i++) {
            //console.log("Linking "+links[i][0]+" and "+links[i][1]);
            graph[links[i][0]].addEdge(graph[links[i][1]]);
        }
        //l.removeBar();
    }
    
}