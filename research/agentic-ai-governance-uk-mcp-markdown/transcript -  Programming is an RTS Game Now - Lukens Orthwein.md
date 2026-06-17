Lukens Orthwein: Founder AI Hacks: Programming is an RTS Game Now
58:56
Um yeah so the the idea behind this talk is sort of um what we uh at channel have
59:05
done to try to take the the best advantage of sort of rethinking how you should do software engineering in this
59:12
world of agentic programming assistance cla etc. Um and really you know the the
59:20
ways in which uh I think many assumptions about what good programming is are now sort of the opposite of what
59:26
you should be doing. Uh and these are sort of what we have have worked through ourselves and found very useful and
59:32
wanted to share with all you guys to give some context. channel AI. We're a consumer entertainment uh AI business.
59:39
Uh and we're really focused on the problem of automating as much as possible of not just software
59:46
development but content development. How do you really create like an endto-end system uh that is pure AI that uh gets
59:53
people to pay you money uh and stay engaged etc. Uh we've had pretty solid
59:58
success with that so far. Um, and it's inspired us to think in our own workflows, how can we just sort of max
1:00:05
this and and be as far ahead of the curve as possible. Um, and chess is an imperfect analogy to what programming
1:00:12
used to be like, but I think the ways that it uh is useful is like yeah, maybe
1:00:18
programming before you wanted to be very linear. You wanted to predict the future. You wanted to design very thoughtfully systems that would be like
1:00:24
robust and work well uh and and be correct. Um, and even if you're trying
1:00:29
to do something sloppily, it's still like a single threaded process where you only are worrying at a given moment
1:00:35
about what's in front of you. Um, and to me, I'm a big fan of real-time strategy
1:00:41
games using Agentic systems. Feels exactly like playing real-time strategy
1:00:46
games to me. Uh, and there are a lot of properties of those games that are very different from chess. Um, one thing and
1:00:52
especially if you look at like highle play uh there is no single aspect that
1:00:57
you can do perfectly and like succeed. You have to be balancing many different things at once. You have to always have
1:01:03
your economy running, your production running, your units doing something productive. You need to be engaging. And
1:01:08
so this notion of like how do you maximally parallelize both what your systems are doing but also your
1:01:14
attention so that you are adding the corrective uh feedback that's necessary as you
1:01:20
learn new things as the map is exposed all this kind of stuff. Um anyway this to me feels like exactly what like
1:01:26
coding with agents is like um and this what we'll talk about. Um so in terms of
1:01:33
like tools we've built just to like ground this in a very simple thing. This
1:01:38
is the LW stuff is just like our linear work trees. Um, a lot of people early on started using realizing how useful git
1:01:44
work trees are when you do coding development. Having separate uh I assume
1:01:50
everybody kind of knows where they are, but in case not like you know it was fine to have one repo on your machine
1:01:55
when you were the only one doing development. Now you need to have like lots and lots of repos on your machine all doing development in parallel. Uh
1:02:02
all compiling separately and like not stepping on each other's toes. Um and so
1:02:08
the combination of like uh using work trees, using task management software,
1:02:13
uh having the actual work itself be portable, um which is what the team bit
1:02:19
comes in, and then like sticking in autonomous agents, one or many different ones on a given workflow. Um the way
1:02:26
that we basically ship stuff, the way I ship stuff, uh is I have an orchestrator agent that's run by Claude usually, but
1:02:33
could be codeex 2. Uh, I try to have as minimal a number of keystrokes as
1:02:39
possible to go from like here's an idea of something that needs to be fixed to work being started on it because I can
1:02:45
course correct that work later. Think like grabbing a unit and just like clicking across the map and you'll come
1:02:50
back later to like make it work effectively. Um, status tracking,
1:02:56
watching your mini map, it's the RTS equivalent uh from the orchestrator of all the different uh spawned workers
1:03:02
that you have working. Uh, and then all those workers being instructed basically to try to go as far as they can, really
1:03:09
put like a really low premium on their time and effort and a high premium on yours. So even if they're going to be
1:03:16
wrong, even if they're going to need to be corrected later, it's better for them to push as far as they can before they
1:03:21
ask for feedback. Uh, so that you can just have a lot of them running in parallel, even if it's wasteful from
1:03:28
like a per per token standpoint. it's like saving you a lot of time or letting you do more things at once. Anyway, so
1:03:34
they try and take everything all the way to a PR uh not just a PR but also like a
1:03:40
summary that's well I'll get into that later anyway. So uh uh and then like how do you take each the results of every
1:03:46
worker who completes something and like feed it back into the system so that the system learns and becomes better again
1:03:51
like without the human having to type a lot of things or doing minimal work so they can do a lot of these things at once. Uh and then other pieces like how
1:03:58
do you tag in other teammates? we'll also get into. Um, but anyway, this is very much like an RTS where you're like
1:04:04
producing units, trying to move them around, trying to constantly adapt to stuff, but also with really high visibility, not just like spawning 20
1:04:11
agents and like hoping that you'll, you know, solve this problem for me, make no mistakes, and it'll just work in the
1:04:16
end, cuz that doesn't actually happen in production. Um, so like some general guidelines or
1:04:24
or or practices uh that that that we use that I use uh at least um but but that
1:04:31
we've we've uh spread through our team is like trying to run almost everything
1:04:36
including scripts that you run because sometimes scripts are a lot better and save on context space than than just
1:04:41
like doing everything by the LLM obviously but running everything from the cloud instances always like never
1:04:47
typing anything outside of it if you can avoid it. Uh having this portability because a lot of times you start work on
1:04:53
a ticket, you start work on something and actually the reason you're stuck on it is cuz someone else on your team or
1:04:58
even maybe another machine. Maybe you're running it locally on your computer and then you're like, "Oh like I got to go home now, but I want this to run
1:05:04
overnight and I make it really easy to move it elsewhere uh and let other people pick it up. Uh maybe it needs
1:05:09
more compute to do something. Whatever. It needs more memory." Um, and uh, and then also just like always running in
1:05:15
dangerously skip permissions mode like whenever possible. Uh, if you can't be running in dangerously skip permissions
1:05:21
mode, do what you need to do to like make a sandbox so you can, but if you're having to give feedback at any regular
1:05:26
pace, like you're going to go really slow. Uh, and then like so what yeah, what do the workers do? As I mentioned
1:05:32
before, they're always trying to go to PR. Uh, they are not rigorously adhering
1:05:38
to like the given spec you do. they're trying to learn and adapt to it as they go because your specs will be wrong. Uh,
1:05:43
and it's okay for them to make assumptions because you can correct them uh as you catch them. Um, and then, you
1:05:50
know, for like, for example, front-end development doing every everything is like pre-baked into the worker spawn. So
1:05:56
boot the local dev server, run tests yourself on it, have it ready and waiting so that the human can just come
1:06:02
and open a browser tab pointing to the right port and they can just test the thing as quickly as possible. Minimizing
1:06:08
the number of human steps that need to be taken and like clicks to just move something forward to the next step uh
1:06:14
step. Um and also just like lots of things baked in that are like what are
1:06:20
things that we know really reliably? the agent's going to be bad about how do we learn about those things, bake them in,
1:06:25
put them in uh to not just like the cloud MD file, but also like broader
1:06:31
reaching graphs that you have of MD files uh which I'll get to later uh to make those things
1:06:38
less of a problem. So, for example, one of like the really obvious things that Claude is super bad at today is
1:06:43
predicting how long it'll take to do something. If you ask it like how long is it going to take to solve this problem be like a maybe like two weeks
1:06:49
of like you know one engineer's work and in practice it takes like one prompt and it can do it in 20 minutes cuz it's
1:06:55
trained on what it would have taken a human to do those things that's all it's like basis for training data the these
1:07:00
systems haven't been around long enough for that to be updated and I think they'll like always be behind anyway so you can take all these things and be
1:07:07
like no no never trust yourself in these ways uh and uh and then also like you
1:07:14
people think a lot and a lot of times it's kind of true that like the code is the source of truth but the code is often like a really expensive source of
1:07:20
truth for the agents to pull context out of and it's actually really cheap especially when you have all the context
1:07:26
loaded in memory to like aggressively document things in a way that benefit
1:07:31
future agents. So uh not just like writing comments in the code but also
1:07:36
structured linked uh um sort of wiki style knowledge knowledgebased files
1:07:42
that will make future agents have an easy time um basically take advantage of
1:07:48
the context as much as you can uh and also helps the visibility of humans and and audit auditability of what you do.
1:07:54
Uh, so macro by default, micro win it counts is another RTS principle. Like
1:08:00
you can't win a game of RT uh like RTS game usually if you're just really good at moving your individual units because
1:08:06
if you didn't make any units, you're just going to lose. Uh so yes, it's important to like deep dive and tunnel
1:08:12
vision into certain things that are really critical. Some tickets for sure take a long time, but anytime you're
1:08:18
like tunnel visioned into something, you should always be thinking, how do I spawn as many other little things that
1:08:23
don't take my cognitive bandwidth as much and just like move those things forward? Um, so that always you're
1:08:30
basically like maxing out your cognitive capacity. Um, and again, like things can wait. You can come back to them like 3
1:08:36
days later. It's not that expensive and you can just ask Claude like remind me what the hell I was doing with this thing. All this stuff is really cheap.
1:08:42
what's expensive but doesn't feel expensive is like not doing these things at the same time. Um anyway, so macro
1:08:50
necessary, micro useful, but you can win honestly in RTS games and I think in a
1:08:56
lot of things, including in programming, if you just macro enough, if you just do enough things, you'll kind of uh
1:09:03
stupidly adjust your way towards something that's good if you're just always really quickly identifying problems and solving them. Um and yeah,
1:09:10
this is gets back to like the high visibility thing. So, one of the things that I really like about you like how I
1:09:16
set things up is it's not like a lot of agents that are kind of tucked away and that you have to like dig in hard to
1:09:22
actually read what their ongoing stream is and what they're actually doing like
1:09:27
like in an RTS game like you click buttons to immediately jump to different key points in the map so you can always
1:09:34
be auditing stuff and always like catch it and correct it quickly if it's a critical thing. That true I that too I
1:09:39
find is like super useful in programming. Uh because again like they're going to make mistakes all the time. They're going to like go in wrong
1:09:46
directions and you definitely save time and value if you catch them early, fix them, course correct. Uh so you should
1:09:51
be kind of like looking around between your different agents, monitoring them while you are also trying to have as
1:09:56
many as you can. Um another thing to this point that I personally like a lot
1:10:02
uh and is like a big thing in RTS games is audio. So, like the only way that you can manage a big army across the whole
1:10:08
map is to have lots of audio cues where it's like your base is under attack or you know this guy's moving or whatever
1:10:15
thing is happening. You don't have to be looking at you can hear and it's like okay I need to put my attention to
1:10:21
this thing and you know based on like a lot of variety these audio cues that you can learn and they're good like
1:10:26
pneumatic devices. Uh what's important? What do I need to act on right away? What don't I? So, like the way I run my
1:10:32
personal setup is I actually have all of my individual agent uh like T-M sessions
1:10:39
mapped to different Warcraft and Starcraft units uh that are colorcoded
1:10:44
and themed based on the type of ticket it is. And then they play the actual sound effects from Warcraft and
1:10:49
Starcraft units. So, I immediately know and like visually identify. I don't even have to read like this tab needs my
1:10:56
attention. This thing's going on. Anyway, like to me it just seems like a natural way of like take advantage of
1:11:01
these and and again like Cludes made all these things for me really quickly as like a side ticket that I was working on over time while I worked on eight other
1:11:08
things. So it's like why not do these things and these these devices pneumatic devices uh or or whatever like cues for
1:11:15
people are really optimized in gaming and they like know what good sound design is to like be memorable and
1:11:20
otherwise catch your attention in different ways. Um, yeah, and like cult
1:11:25
use of color, icons, anything that's just like quicker to read and process because I actually do think like these
1:11:31
things matter a lot, especially if you're trying to uh really aggressively get a lot of stuff done and the sky is
1:11:37
kind of the limit in how you can do that stuff. Another thing we built internally is like an APM tracker. Uh, and I'll
1:11:43
just show quickly here. Um,
1:11:53
so and this this is Warcraft 3, which is like one of the lower APM requiring professional RTS games, but this is what
1:11:59
it looks like to actually play this game well uh at the at the top level. And one of the things that you'll notice is like
1:12:06
no APM is not the uh the thing that like if you max it, you're the best player in
1:12:13
the world, but nobody is good who doesn't have high APM. And so you can just kind of take that as a mental
1:12:19
rubric like if I'm like thinking and like typing slowly and like am I if
1:12:25
this was a competition, would I really be the best? Like do I really need to take that much time in everything I'm doing? and how much can I just take like
1:12:32
lots of little micro decisions and you know fall toward the right uh the right
1:12:38
goal or toward making things better. Um anyway, so this is just something like we we you know each of us run like
1:12:45
personally on our computers and keep an eye on and it's just like just keep track of like are things moving and this
1:12:52
this APM is not like clicks you have because I don't think that's like a great tracker for for for agent use. We
1:12:58
use tool you tool calls. It's like how many tool calls are your agents doing per minute? Uh this minute, this five
1:13:05
minutes, this hour, this day, this seven days, like how do you max all those things and have high numbers. Um and
1:13:12
again, it's like it's it's one metric among many, but it's how are you actually being really productive or are
1:13:18
you really doing the most you could be doing if you have a low APM? Uh probably not. So otherwise like things probably a
1:13:24
lot of people know uh easy way to to use tokens more effectively is just like do
1:13:30
a lot of things in parallel do different things with the same agent do different agents in parallel it will uh invariably
1:13:37
like for complex tasks usually give you a better outcome than if you did it by yourself and just like in an RTS like
1:13:43
you should be spending your resources you should never have your claude tokens like sitting unused that's really inefficient economy like use them all
1:13:50
every hour period that you man. Um, knowledge base. This is like a really
1:13:55
big thing that that for us I think is still like somewhat early on. But, uh, this whole presentation I made and
1:14:02
started the exact same way that, uh, I'm just describing how I do tickets, which is I went to Claude, I took what France
1:14:09
asked me to talk about, I pasted it in, I said, "Look at our knowledge base and how we do stuff." And put together a
1:14:14
PowerPoint presentation based on the philosophies embedded in there and like what I've told you before. and he didn't
1:14:19
like oneshot it, but it's like I maybe did like 15 edits to it, you know, and and got to this presentation.
1:14:26
Uh, and then I refed it all back into the knowledge base and said like learn everything that I've said and all the the the advice I've given and
1:14:33
corrections I've given and like make those better instilled in the knowledge base. And this knowledge base is basically just because like linked docs
1:14:39
are much faster diverse by LLMs. And so uh and you can encode everything
1:14:45
including business knowledge and indeed like Claude and and Codex are really good at coming up with features and stuff if they have enough knowledge
1:14:50
about your business. Uh so trying to build this up in an automated way is super useful. People come up with their own tickets. Uh because if you have
1:14:57
something you could do everybody you should just like do it. Everybody should be full stack all the time. Uh be
1:15:03
reactive. Uh and uh even if agent does it way worse than you or slower than
1:15:09
you, it's still better to have it do it. And uh it's easy to change things when they're screwed up. Satisficing is a
1:15:15
word from economics is like do things satisfi like enough but not perfect. Uh
1:15:21
really really key principle for like everything. Uh mix different ticket sizes at the same time. Uh you know in
1:15:28
like we we've three and a halfx our output uh PRs per engineer per month. uh
1:15:35
both because LM have made ourselves better, but like when we like really adopted this stuff broadly with everyone on the team this last month, we grew
1:15:41
another 60% in our PRs per engineer per month. So like you're not going to get a lot smarter, but the thing you can train
1:15:47
on yourself is like how do I act like people who are good at doing these kinds of things really well like RTS pro
1:15:54
players? What does it look like to be like optimal in this and how can I learn the methods of doing it just like
1:15:59
program like an RTS pro? Thank you.
1:16:06
Okay, I think that's all we have. Um, now I think Vikica, we have cookies, ice