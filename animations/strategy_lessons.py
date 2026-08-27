"""Manim scenes for every Wize Wizard guided lesson.

These scenes are intentionally short, visual teaching examples. They do not replace the
interactive live tools; they explain what the user is about to do and why.
"""
try:
    from manim import *
except ImportError:
    raise SystemExit("Manim is not installed. Install with: pip install 'wize-wizard[animation]'")


def box(label, width=3.0, height=0.9, font_size=24):
    r = RoundedRectangle(width=width, height=height, corner_radius=0.12)
    t = Text(label, font_size=font_size).move_to(r)
    return VGroup(r, t)


class WhyLadder(Scene):
    def construct(self):
        self.play(Write(Text("Every WHY is another complete statement", font_size=38).to_edge(UP)))
        items = [
            ("NEED / GOAL", "make money → buy a car"),
            ("WHY 1 / WISH", "reliable transportation → get to work"),
            ("WHY 2 / DREAM", "buy a house → reduce rent"),
            ("WHY 3 / FANTASY", "financial freedom → control my time"),
        ]
        nodes = VGroup(*[box(a, 4.5, 0.85, 20) for a,_ in items]).arrange(DOWN, buff=0.5).shift(LEFT*2.6)
        desc = VGroup(*[Text(b, font_size=20) for _,b in items])
        for d,n in zip(desc,nodes): d.next_to(n, RIGHT, buff=0.4)
        self.play(FadeIn(nodes[0]), Write(desc[0]))
        for i in range(1,4):
            arrow=Arrow(nodes[i-1].get_bottom(),nodes[i].get_top(),buff=.08)
            why=Text("WHY?",font_size=18).next_to(arrow,RIGHT,buff=.1)
            self.play(GrowArrow(arrow),Write(why),FadeIn(nodes[i]),Write(desc[i]))
        self.wait(1)


class PERTStress(Scene):
    def construct(self):
        self.play(Write(Text("PERT: plan with three estimates", font_size=40).to_edge(UP)))
        vals=[("BEST",6),("MOST LIKELY",12),("WORST",24)]
        bars=VGroup()
        for label,v in vals:
            b=Rectangle(width=v/5,height=.7)
            txt=Text(f"{label}: {v}h",font_size=22).next_to(b,LEFT)
            bars.add(VGroup(b,txt))
        bars.arrange(DOWN,buff=.7).shift(RIGHT*.8)
        self.play(LaggedStart(*[GrowFromEdge(x[0],LEFT) for x in bars],lag_ratio=.2),LaggedStart(*[Write(x[1]) for x in bars],lag_ratio=.2))
        f=Text("Expected = (Best + 4×Likely + Worst) / 6",font_size=26).to_edge(DOWN)
        self.play(Write(f)); self.wait(1)


class CommunicationChannels(Scene):
    def construct(self):
        self.play(Write(Text("Communication: structure the coordination",font_size=38).to_edge(UP)))
        people=VGroup(*[Dot(radius=.12) for _ in range(8)]).arrange_in_grid(rows=2,buff=.8).shift(LEFT*3)
        self.play(FadeIn(people))
        lines=VGroup(*[Line(people[i],people[j],stroke_width=1) for i in range(8) for j in range(i+1,8)])
        self.play(Create(lines),run_time=1.5)
        raw=Text("All-to-all channels grow quickly",font_size=24).next_to(people,DOWN)
        self.play(Write(raw)); self.play(FadeOut(lines))
        sup1=Star(n=5,outer_radius=.22).move_to(people[0]); sup2=Star(n=5,outer_radius=.22).move_to(people[4])
        structured=VGroup(*[Line(people[0],people[i],stroke_width=3) for i in range(1,4)],*[Line(people[4],people[i],stroke_width=3) for i in range(5,8)],Line(people[0],people[4],stroke_width=3))
        self.play(FadeIn(sup1,sup2),Create(structured))
        self.play(Transform(raw,Text("Local supervisors reduce coordination paths",font_size=24).next_to(people,DOWN))); self.wait(1)


class StrategyLoop(Scene):
    def construct(self):
        title=Text("Strategy is judgment + logic + computation + action",font_size=34).to_edge(UP)
        labels=["QUESTION","ASSUMPTION","EVIDENCE","MODEL","NEED GOAL","EXECUTE","LEARN"]
        nodes=VGroup(*[box(x,2.0,.7,17) for x in labels]).arrange_in_grid(rows=2,buff=.55)
        self.play(Write(title)); self.play(LaggedStart(*[Create(n) for n in nodes],lag_ratio=.08)); self.wait(1)


class BCGExperience(Scene):
    def construct(self):
        self.play(Write(Text("BCG: relative position is only the start",font_size=38).to_edge(UP)))
        a=box("Your share 15%",3,1); b=box("Leader 25%",3,1).next_to(a,RIGHT,buff=1)
        self.play(FadeIn(a,b)); rms=Text("Relative Market Share = 15 / 25 = 0.60",font_size=28).next_to(VGroup(a,b),DOWN,buff=.8); self.play(Write(rms))
        chain=Text("Experience → Cost → Position → Cash → Capital allocation",font_size=25).to_edge(DOWN); self.play(Write(chain)); self.wait(1)


class MECEIssueTree(Scene):
    def construct(self):
        self.play(Write(Text("MECE: split the problem without obvious gaps",font_size=36).to_edge(UP)))
        root=box("Sales decline",3,1).shift(UP*1.7)
        children=VGroup(*[box(x,2.2,.75,19) for x in ["Market","Customer","Economics","Execution"]]).arrange(RIGHT,buff=.35).shift(DOWN*.8)
        self.play(FadeIn(root));
        for c in children: self.play(GrowArrow(Arrow(root.get_bottom(),c.get_top(),buff=.08)),FadeIn(c),run_time=.35)
        self.wait(1)


class FiveForces(Scene):
    def construct(self):
        center=box("INDUSTRY",2.5,1).move_to(ORIGIN)
        labels=["Rivalry","New entrants","Substitutes","Suppliers","Buyers"]
        pos=[UP*2.2,LEFT*3,RIGHT*3,DOWN*2+LEFT*2,DOWN*2+RIGHT*2]
        nodes=[box(l,2.2,.7,19).move_to(p) for l,p in zip(labels,pos)]
        self.play(FadeIn(center));
        for n in nodes: self.play(FadeIn(n),GrowArrow(Arrow(n.get_center(),center.get_center(),buff=.7)),run_time=.35)
        self.play(Write(Text("Profit pressure comes from more than direct rivals",font_size=24).to_edge(DOWN))); self.wait(1)


class MarketConcentration(Scene):
    def construct(self):
        title=Text("Market concentration in plain English",font_size=40).to_edge(UP); self.play(Write(title))
        vals=[25,20,15,10,7]
        bars=VGroup(*[Rectangle(width=.75,height=v/8).shift(RIGHT*(i-2)*1.1+DOWN*.5) for i,v in enumerate(vals)])
        labels=VGroup(*[Text(f"{v}%",font_size=18).next_to(b,UP,buff=.1) for b,v in zip(bars,vals)])
        self.play(LaggedStart(*[GrowFromEdge(b,DOWN) for b in bars],lag_ratio=.12),FadeIn(labels))
        cr=Text("Four-Firm Concentration Ratio = 25+20+15+10 = 70%",font_size=23).to_edge(DOWN)
        self.play(Write(cr)); self.wait(.5); self.play(Transform(cr,Text("Herfindahl-Hirschman Index squares each share before adding",font_size=23).to_edge(DOWN))); self.wait(1)


class ROICvsWACC(Scene):
    def construct(self):
        t=Text("Is the return above the financing hurdle?",font_size=38).to_edge(UP); self.play(Write(t))
        roic=box("Return on Invested Capital\n12%",4,1.3,22).shift(LEFT*2.5)
        wacc=box("Weighted Average Cost of Capital\n9%",4,1.3,22).shift(RIGHT*2.5)
        self.play(FadeIn(roic,wacc)); arrow=Arrow(wacc.get_top(),roic.get_top(),path_arc=-1.5); self.play(GrowArrow(arrow))
        self.play(Write(Text("12% − 9% = +3% spread → potential value creation",font_size=25).to_edge(DOWN))); self.wait(1)


class MonteCarloRisk(Scene):
    def construct(self):
        self.play(Write(Text("Monte Carlo: replace one forecast with a distribution",font_size=34).to_edge(UP)))
        axes=Axes(x_range=[0,30,5],y_range=[0,1,.2],x_length=9,y_length=4,tips=False)
        curve=axes.plot(lambda x: max(0,1-abs(x-15)/12),x_range=[3,27])
        self.play(Create(axes),Create(curve));
        for x,lbl in [(12,"P50"),(19,"P80"),(24,"P95")]:
            line=axes.get_vertical_line(axes.c2p(x,.3),line_config={"stroke_width":2}); self.play(Create(line),Write(Text(lbl,font_size=18).next_to(line,UP,buff=.1)),run_time=.3)
        self.wait(1)


class ConstraintsFlow(Scene):
    def construct(self):
        self.play(Write(Text("Improve the bottleneck first",font_size=40).to_edge(UP)))
        steps=VGroup(*[box(x,2.4,.8,18) for x in ["Input","Process A","BOTTLENECK","Process C","Output"]]).arrange(RIGHT,buff=.25)
        self.play(LaggedStart(*[FadeIn(x) for x in steps],lag_ratio=.1))
        queue=VGroup(*[Square(.25) for _ in range(7)]).arrange(RIGHT,buff=.05).next_to(steps[2],UP)
        self.play(FadeIn(queue)); self.play(Write(Text("Work piles up before the constraint",font_size=24).to_edge(DOWN))); self.wait(1)


class IntegratedDecision(Scene):
    def construct(self):
        self.play(Write(Text("Do not stop at the first good-looking metric",font_size=36).to_edge(UP)))
        labels=["Position","Economics","Five Forces","Risk","Future options"]
        nodes=VGroup(*[box(x,2.3,.75,18) for x in labels]).arrange(RIGHT,buff=.25).shift(UP*.5)
        self.play(LaggedStart(*[FadeIn(n) for n in nodes],lag_ratio=.12))
        for a,b in zip(nodes[:-1],nodes[1:]): self.play(GrowArrow(Arrow(a.get_right(),b.get_left(),buff=.08)),run_time=.25)
        final=box("WIZE NEED\nI need to ___ so that I can ___",5,1.2,21).next_to(nodes,DOWN,buff=1)
        self.play(FadeIn(final)); self.wait(1)
