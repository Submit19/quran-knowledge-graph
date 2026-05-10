# Transcript: https://www.youtube.com/watch?v=O2bBWDoxO4s

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 1073

---

**[00:02]** No,  
**[00:07]** >> I think we're live. What's up, Jeff?  
**[00:09]** >> What's up, Dex?  
**[00:11]** >> Uh, I'm really jealous of your of your  
**[00:13]** DJ setup over there. That's uh pretty  
**[00:15]** incredible.  
**[00:17]** >> It's been a while. Thanks, mate. Like, I  
**[00:19]** remember um when I first caught up with  
**[00:22]** you in San Fran, probably what June,  
**[00:25]** July, rocking into a meetup and like go  
**[00:28]** to Allison. It's like here's some  
**[00:30]** pre-alpha. If you run it in a loop, you  
**[00:32]** get crazy outcomes. And this was with  
**[00:34]** Sonnet  
**[00:36]** 45. And now we're up to Opus 45.  
**[00:39]** >> No, dude. This was not Sonnet 45. This  
**[00:41]** was in May. This would have been like  
**[00:43]** Sonnet 35, I think.  
**[00:44]** >> Yeah, it was. Anyway, it was it was  
**[00:47]** cooked back then. Six months later, as  
**[00:50]** the model gets better, uh this the the  
**[00:53]** techniques  
**[00:55]** um there's been a few attempts to turn  
**[00:57]** it into products.  
**[00:59]** Um, but I I don't think that will work.  
**[01:03]** Um, because I see LLM's amplifier of  
**[01:07]** operator skill.  
**[01:09]** >> Yep.  
**[01:09]** >> Um, and  
**[01:12]** if you just set it off and run away,  
**[01:15]** you're not going to get a great as great  
**[01:17]** of an outcome. um you really want to  
**[01:21]** actually babysit this thing and then get  
**[01:23]** really curious why it did that thing and  
**[01:26]** then try to tune that behavior in or out  
**[01:29]** and really think about it and never  
**[01:31]** blame the model and always be curious  
**[01:33]** about what's going on. So it's really  
**[01:35]** highly supervised.  
**[01:38]** >> Highly super. Yeah, you guys were  
**[01:40]** talking with Matt today was like human  
**[01:41]** on the loop is better than human in the  
**[01:43]** loop, which is like don't ask me, but  
**[01:45]** I'm going to go poke it and pro it and  
**[01:47]** test it and I might stop you at certain  
**[01:49]** points, but I'm not being the model's  
**[01:50]** not deciding when and how that happens.  
**[01:53]** >> Correct. So, it's it's really cute that  
**[01:55]** Anthropic has made the uh Ralph plugin,  
**[01:59]** which is nice.  
**[02:01]** Um, so that it's starting to cross the  
**[02:03]** chasm, but I do have some concerns that  
**[02:05]** people will just like try the official  
**[02:08]** plugin and go, "That's not it." And like  
**[02:10]** you've you've you've poked in the  
**[02:12]** internals. I've I've we sat down and  
**[02:15]** you've done it. You you see the  
**[02:17]** concepts. It's like some of the ideas  
**[02:19]** behind human layer.  
**[02:21]** >> It's um you say that it's not it. So how  
**[02:24]** is it not it, Dex?  
**[02:26]** >> Okay. So, I'm going to talk about what  
**[02:28]** we actually want to do today, which is  
**[02:30]** like  
**[02:31]** >> I have two GCP VMs,  
**[02:34]** and in both of them, we have this specs,  
**[02:36]** and they both have a repo checked out.  
**[02:38]** Um, this one actually doesn't even have  
**[02:40]** a loop dash yet. This just has the like  
**[02:42]** slashwigum  
**[02:45]** create loop or whatever. I forgot what  
**[02:47]** the exact thing is. We're going to go  
**[02:47]** set it up today. I haven't actually  
**[02:49]** turned this on yet. Um, but I've created  
**[02:52]** these two git repos. One has a prompt.  
**[02:54]** MD and a loop.sh sh and it will  
**[02:56]** eventually create this implementation  
**[02:58]** plan. This is like vanilla Ralph from  
**[03:00]** the Jeff recipe, right? And so I've got  
**[03:04]** in this shell I have my loop.sh,  
**[03:07]** which is literally just run claude in  
**[03:09]** yolo mode, cat the prompt in and let it  
**[03:12]** go do its thing.  
**[03:14]** >> Yeah. Bump your font uh bigger by the  
**[03:16]** way. Triple size. What's bigger? Bigger.  
**[03:18]** Bigger.  
**[03:18]** >> Yeah. Yeah. Yeah. And I'm actually going  
**[03:19]** to close some of these terminals. Um,  
**[03:22]** and then each of these have um,  
**[03:28]** let's see if we can pull this down.  
**[03:29]** Yeah, each of these have a so there's  
**[03:31]** two directories. There's two git repos  
**[03:33]** I've made. One to test the anthropic  
**[03:36]** version.  
**[03:38]** Uh, and one to test the uh, I'll call it  
**[03:41]** the Jeff version of Ralph. Um, so we've  
**[03:45]** got the bash one and then we've got the  
**[03:48]** plug-in one.  
**[03:51]** And so these both have received they're  
**[03:52]** just empty repos. Um I'm going to add  
**[03:55]** the loop and the prompt. We'll look at  
**[03:56]** the prompt in a sec. But then we've got  
**[03:59]** these just like specs for a project that  
**[04:02]** I was hacking on called customark which  
**[04:04]** if you remember Kubernetes and the  
**[04:06]** customized world. It's sort of a uh  
**[04:09]** customization pipeline for like  
**[04:12]** incrementally building markdown files  
**[04:14]** with like patches and stuff.  
**[04:17]** Um, so anyways, they're both getting the  
**[04:19]** same set of specs and they're both  
**[04:22]** basically being instructed to uh  
**[04:26]** run. They both get the same prompt,  
**[04:28]** which is like,  
**[04:33]** oh my god. And actually, I guess this  
**[04:35]** one will also get implementation plan,  
**[04:37]** right?  
**[04:38]** >> Yeah.  
**[04:39]** >> Assuming we have the same prompt. And  
**[04:41]** the prompt is essentially I'll just push  
**[04:44]** it and go get it. Um,  
**[04:47]** >> while you go get it now, yeah,  
**[04:49]** >> in that diagram you have GCP  
**[04:52]** >> folks,  
**[04:53]** >> we uh we've been at AGI for a very long  
**[04:56]** time. If you define AGI as disruptive  
**[04:59]** for software engineers, at least six  
**[05:01]** months now, and these models are just  
**[05:03]** getting better. Now,  
**[05:04]** >> yeah,  
**[05:05]** >> the GCP thing I see people go, oh, what  
**[05:07]** about the sandbox sandboxing dangerously  
**[05:10]** allow all? Think about it. Dangerously  
**[05:13]** all is literally like put deliberately  
**[05:16]** injecting humans into the loop. You  
**[05:19]** don't want to inject yourself into the  
**[05:21]** loop because that's essentially not AGI.  
**[05:24]** You're dumbing it down.  
**[05:25]** >> But it is kind of dangerous to do  
**[05:28]** things. So the fact that you're running  
**[05:29]** on a GCP VM  
**[05:32]** is key, right? You you want to you want  
**[05:35]** to enable all the tools,  
**[05:38]** >> but everything about it.  
**[05:40]** >> And remember the lethal trifecta, right?  
**[05:41]** is like  
**[05:42]** >> got to remember the loop  
**[05:43]** >> trifecta  
**[05:45]** >> is  
**[05:47]** access to the network.  
**[05:49]** >> Yeah.  
**[05:50]** >> And then access to private data.  
**[05:52]** >> Correct.  
**[05:53]** >> So  
**[05:54]** >> we are giving it access to do everything  
**[05:55]** which means it can search the web which  
**[05:57]** means it can accidentally stumble on  
**[05:58]** untrusted input. We're giving it access  
**[06:00]** to the network to because it needs to do  
**[06:03]** things. I don't know search web whatever  
**[06:04]** it is. And we're giving it we're not  
**[06:06]** giving it access to private data. So  
**[06:07]** there here's why we're safe is this is  
**[06:09]** running in like a dev cluster in GCP and  
**[06:12]** I think the only thing on there is like  
**[06:14]** the default IM key which can literally  
**[06:16]** like look up information about the  
**[06:18]** instance.  
**[06:19]** >> You can look at this as layers of onion  
**[06:23]** layers of the security onion.  
**[06:25]** >> Uh so like if you run dangerously allow  
**[06:29]** all from your local laptop, congrats.  
**[06:31]** They they go nab your Bitcoin wallet if  
**[06:33]** it's on your computer. They steal your  
**[06:35]** Slack authentication cookies, GitHub  
**[06:38]** cookies, and they pivot, right? That  
**[06:39]** that's that's terrible.  
**[06:41]** >> But if you create a custom purpose VM or  
**[06:45]** an ephemeral instance just for this,  
**[06:48]** >> you start restricting its network abil  
**[06:51]** network connectivity and you do all the  
**[06:54]** things that you should do as a security  
**[06:55]** engineer. The next thing you know is  
**[06:58]** like okay it's not what if it's like if  
**[07:02]** it gets when it gets popped. I develop  
**[07:06]** on the basis that it's a when so the  
**[07:08]** blast radius is if that GCP is like the  
**[07:12]** worst thing it is because this is not  
**[07:14]** public IP.  
**[07:15]** >> Yep.  
**[07:16]** >> Um there is no really absolutely  
**[07:19]** terrible thing. Okay. And we've given it  
**[07:21]** restrict. The only permissions on this  
**[07:23]** box are my cloud API keys and deploy  
**[07:25]** keys to push to the two GitHub repos.  
**[07:28]** >> Correct. Proper security engineering.  
**[07:31]** >> It's not if it gets popped. It's not if  
**[07:33]** it gets popped, it's when it gets  
**[07:35]** popped. And what is the blast radius?  
**[07:38]** >> So,  
**[07:38]** >> this is however not an invitation to go  
**[07:40]** pop my GCP VMs. I will not be sharing  
**[07:42]** the IP addresses.  
**[07:45]** If you want to uh share API keys with  
**[07:47]** me, Dex, I always need some.  
**[07:49]** >> Uh you know what, man? I think you have  
**[07:52]** I heard you got a lot of tokens popping  
**[07:54]** around over there. If anything, you  
**[07:56]** should be bringing me some tokens.  
**[07:58]** >> Facts.  
**[08:00]** >> Um all right, let's look at this prompt.  
**[08:02]** Yeah.  
**[08:03]** >> Yeah. Let's look at the concept of the  
**[08:05]** prompt. Um look, look at the prompt.  
**[08:08]** >> So, here's what I'm using.  
**[08:12]** This is my take on the original Ralph  
**[08:14]** prompt. Sorry, let me let me my I have  
**[08:16]** T-Mox inside T-Mox here, so it's getting  
**[08:18]** a little  
**[08:18]** >> That's fine. Okay, let's look at zero A,  
**[08:21]** right?  
**[08:22]** >> Yep. So, this is you got to think like a  
**[08:25]** like a like a C or C++ engineer and you  
**[08:29]** got to think of context windows as  
**[08:31]** arrays because they are they're  
**[08:33]** literally arrays.  
**[08:34]** >> Context windows are arrays.  
**[08:37]** you the a tool the chat when you chat  
**[08:42]** with the LLM you allocate to the array  
**[08:45]** when you get when it executes bash or  
**[08:48]** another tool it autoallocates the array.  
**[08:51]** >> Yep.  
**[08:53]** >> So getting into something like context  
**[08:57]** engineering I heard there's a guy who  
**[09:00]** knows a thing or two about that  
**[09:01]** definition. Hey, I just talked to people  
**[09:04]** like you who uh who who knew things and  
**[09:07]** put a name on a thing that hundreds of  
**[09:08]** people were doing.  
**[09:10]** >> But yeah, context engineering is all  
**[09:12]** about designing this array.  
**[09:14]** >> It's all about the array. So, and  
**[09:16]** thinking about how LLMs are essentially  
**[09:19]** a sliding window over the array  
**[09:23]** and the less that that window needs to  
**[09:26]** slide, the better. There is no memory  
**[09:29]** server side.  
**[09:31]** It's it's literally that an array. The  
**[09:34]** array is the memory. So you want to  
**[09:36]** allocate less.  
**[09:38]** So let's go back to the prompt.  
**[09:40]** >> Yep.  
**[09:43]** >> Zero way. We're deliberately  
**[09:45]** allocating. This is the key. Deliberate  
**[09:48]** malicking  
**[09:50]** uh context about your application.  
**[09:53]** >> We're going to say we're just going to  
**[09:54]** have 5,000ish tokens that are dedicated  
**[09:57]** for like here's what we're building and  
**[09:58]** we want that in every time.  
**[10:00]** >> Yeah. This could be uh index h index.mmd  
**[10:05]** or readme.md which is a whole bunch of  
**[10:07]** hyperlinks out to different specs.  
**[10:10]** >> Yep.  
**[10:12]** >> Enough to like tease and tickle the  
**[10:14]** latent space that like there are files  
**[10:16]** there.  
**[10:17]** >> So you can either go for an index or if  
**[10:22]** Ralph starts being dumb you can go for  
**[10:24]** like deliberate injection.  
**[10:27]** So you can at specs, right? And that  
**[10:29]** will just be just to list that out.  
**[10:33]** >> Correct. You mentioned a file name. It  
**[10:35]** the the tool registration for read file  
**[10:37]** is going to go oh is there a file on  
**[10:39]** that? I'm going to read it.  
**[10:41]** >> Mhm.  
**[10:42]** >> So you can give a directory path. You  
**[10:44]** can give it like a direct file. So that  
**[10:46]** is the key. So if we go back to your  
**[10:48]** context window diagram.  
**[10:51]** >> Yeah.  
**[10:52]** >> Right. Think about this. So it's kind of  
**[10:55]** like you're allocating the array  
**[10:56]** deliberately. So the first couple first  
**[10:59]** first couple allocations uh is about the  
**[11:02]** actual application.  
**[11:04]** >> Mhm.  
**[11:06]** >> And every loop  
**[11:08]** that allocation is always there. Now  
**[11:12]** LLM engineering is kind of tarot science  
**[11:15]** bit like tarot card reading. It's not  
**[11:18]** really a science, but to me on vibes, it  
**[11:21]** felt like it was a little bit more  
**[11:22]** deterministic if I allocated the first  
**[11:26]** couple things deterministically.  
**[11:31]** >> Yeah.  
**[11:32]** >> Um, now once you've got that, we go on  
**[11:35]** to essentially our next level line in  
**[11:39]** the spec. So like the first one is like  
**[11:40]** deliberate malicking on every loop in  
**[11:43]** the array.  
**[11:44]** >> Yep.  
**[11:46]** >> Okay. So, now we got like a to-do list  
**[11:49]** type thing,  
**[11:51]** >> like an implementation plan.  
**[11:54]** >> Yeah.  
**[11:55]** >> Now, something that's kind of missing in  
**[11:58]** there is like pick one.  
**[12:02]** >> Oh, it says implement the single highest  
**[12:04]** priority feature.  
**[12:05]** >> Oh, yeah. Okay. Yeah, I see that. Sorry.  
**[12:08]** Um,  
**[12:09]** >> that's the idea. Yeah. So, a lot of the  
**[12:12]** people that do these multi-stage things,  
**[12:14]** let's go back to the context window  
**[12:16]** diagram. They do these multi-stage  
**[12:17]** things.  
**[12:19]** >> Well, what you want to do is for each  
**[12:22]** one item,  
**[12:24]** reset the goal. Remalik the objective.  
**[12:27]** >> Yes.  
**[12:28]** >> Cuz what you do is  
**[12:30]** >> imagine you have your somewhere down  
**[12:32]** here is the line of like where like  
**[12:34]** performance degrades noticeably.  
**[12:37]** >> Correct. There is a dumb zone. You  
**[12:38]** should stay out of it. if the dumb zone  
**[12:41]** is down here and it's very dependent on  
**[12:43]** where this line is depending on what  
**[12:44]** you're doing and if how your trajectory  
**[12:46]** is and how much you're reading and all  
**[12:47]** of this. Um but if you ask it to do too  
**[12:50]** much in the working context then some of  
**[12:53]** your results are going to be dumb and  
**[12:54]** especially the important part where it's  
**[12:55]** like okay I've made all the changes let  
**[12:57]** me run the tests and then the tests are  
**[12:58]** failing and it's like scrambling and  
**[13:00]** flailing to try to get everything  
**[13:01]** working. You kind of want to have this  
**[13:04]** and then like a little bit of headroom  
**[13:06]** also for like finalizing like doing the  
**[13:08]** get commands pushes and making sure that  
**[13:10]** all works. You want to have that all  
**[13:12]** happening in the smart zone.  
**[13:14]** >> This is the human in the loop uh human  
**[13:16]** on the loop not in the loop. So I I I  
**[13:20]** you we we set this up. We architect this  
**[13:24]** loop in in this way and you can either  
**[13:27]** go complete AFK or you can be on the  
**[13:32]** loop. The what you just draw drew there  
**[13:34]** is on the loop. I when I'm doing this I  
**[13:38]** always leave myself a little bit of  
**[13:39]** space for juicing like like when I'm  
**[13:42]** reviewing the work. This is when I  
**[13:44]** software instead of Lego bricks is now  
**[13:46]** clay. So, this is where I I'll do my  
**[13:48]** like final wrap-up steering or I just  
**[13:51]** throw it away and then I  
**[13:53]** >> get reset hard and I adjust my technique  
**[13:56]** and let it rip again.  
**[13:58]** >> So, you're saying you might even in the  
**[13:59]** early days you might just run one  
**[14:01]** iteration of this loop and then actually  
**[14:03]** sit here and check it like have it  
**[14:05]** basically for input between looping  
**[14:07]** again. Right.  
**[14:09]** >> So, like there's a reason I did the live  
**[14:12]** the live streams. It's literally I use  
**[14:14]** it as a cheeky portable monitor on my  
**[14:16]** phone. I'm doing like housework and  
**[14:18]** stuff and it's like a as like a portable  
**[14:21]** monitor and I check in. I watch it. You  
**[14:24]** start to notice patterns like and you  
**[14:26]** start to anamorphize  
**[14:28]** certain tendencies like Opus 45 doesn't  
**[14:32]** have high anxiety with the context  
**[14:34]** window gets  
**[14:35]** >> but it does seem to be forgetful  
**[14:39]** of some objectives. Um but  
**[14:43]** So, I wanna I want to quickly um because  
**[14:45]** I know you have a limited amount of  
**[14:47]** time, I want to quickly go through the  
**[14:49]** architecture of the anthropic plugin and  
**[14:51]** how it's different and then I really  
**[14:52]** want to get these things kicked off  
**[14:54]** because I want people to start seeing  
**[14:55]** how they how they actually work.  
**[14:57]** >> Um, and so in the Ralph Wigum plugin,  
**[15:00]** rather than like do the very first  
**[15:02]** thing,  
**[15:04]** um, so it's it we're going to use the  
**[15:06]** exact same prompt for both of them  
**[15:08]** because we want to like change as much  
**[15:09]** as little as possible. But what's going  
**[15:12]** to happen in the  
**[15:14]** uh anthropic plugin is basically  
**[15:17]** whenever it get forget where the  
**[15:19]** performance line is, but whenever it  
**[15:21]** gets to the end and you have your like  
**[15:23]** final assistant user message,  
**[15:25]** >> it's got a promise. It it uses a  
**[15:27]** promise. So the user's got to do a  
**[15:29]** promise and it it relies on the LLM to  
**[15:32]** promise that it's completed.  
**[15:35]** >> Yeah.  
**[15:36]** So you have your final message and then  
**[15:38]** basically unless unless this contains  
**[15:41]** the promise. Sorry, let's just drop this  
**[15:43]** in.  
**[15:47]** If it's no,  
**[15:50]** then we basically inject like the the  
**[15:53]** hook injects a new user message that is  
**[15:56]** just like  
**[15:59]** prompt. MD again, which is then going to  
**[16:01]** cause this stuff to be reallocated and  
**[16:04]** like happen again. And then you get  
**[16:06]** things like compaction and all this  
**[16:08]** stuff. I want compaction is the devil.  
**[16:10]** Dex.  
**[16:11]** >> Yeah. At some point you get compacted  
**[16:13]** here  
**[16:14]** >> and then instead of having all of the  
**[16:16]** context you end up with okay. You were  
**[16:18]** running some tools and then you get  
**[16:20]** compacted  
**[16:21]** >> and then  
**[16:22]** >> and then you have the model summary.  
**[16:24]** >> Yeah.  
**[16:27]** >> Of like what the model thinks is  
**[16:28]** important and then you keep going.  
**[16:31]** >> Correct. until you get your final  
**[16:32]** message and then this process repeats.  
**[16:37]** >> Yeah.  
**[16:37]** >> And so in these very different behavior  
**[16:40]** >> it's a it turns this is why I say  
**[16:42]** deterministic  
**[16:44]** >> because it's essentially  
**[16:46]** uh one is one model has zero auto  
**[16:49]** compaction ever. The other one is using  
**[16:52]** auto compaction. So the one auto  
**[16:54]** compaction is lossy. It could remove the  
**[16:57]** specs.  
**[16:59]** um it can remove the task and goal and  
**[17:01]** objective and with this with the Ralph  
**[17:04]** loop the idea is you set one goal one  
**[17:07]** objective in that context window and so  
**[17:09]** it knows when it's done if you keep  
**[17:12]** extending the context window forever the  
**[17:15]** >> you you lose your deterministic  
**[17:17]** allocation  
**[17:18]** >> you lose your deterministic allocation  
**[17:20]** and more more so let's assume the  
**[17:22]** garbage collection hasn't run it hasn't  
**[17:24]** been compacted  
**[17:26]** >> that window has to slide over two or  
**[17:29]** three goals  
**[17:31]** and some of those goals have already  
**[17:32]** been actually completed.  
**[17:35]** >> Mhm.  
**[17:38]** >> One context window, one activity, one  
**[17:41]** goal and that goal can be very fine  
**[17:43]** grain like do a refactor, add structured  
**[17:45]** logging, what else have you like and you  
**[17:48]** can have multiple of these running. You  
**[17:49]** can have multiple Ralph loops running.  
**[17:53]** >> Um, okay. So, I'm on my Ralph plug-in  
**[17:55]** one. I'm gonna run claw and I'm going to  
**[17:57]** kick off this loop for the um for the  
**[17:59]** other one. So, we're going to do Ralph  
**[18:01]** Wigum Ralph loop  
**[18:05]** read  
**[18:09]** and then our what is it? Uh prom. What  
**[18:11]** is the name of the flag? Sorry.  
**[18:13]** >> Uh promise or something. Yeah.  
**[18:16]** >> Completion promise.  
**[18:18]** >> Completion promise. Yeah.  
**[18:31]** And this is going to turn on the hook  
**[18:32]** and it's going to start working. And  
**[18:34]** over here, I'm going to kick off our  
**[18:37]** loop.sa. Oh, I think I might have.  
**[18:42]** Uh, I think I might need to grab the  
**[18:43]** prompt.  
**[18:45]** >> Yeah. All right. So the number thing to  
**[18:47]** think about this is this is essentially  
**[18:49]** the Ralph plugin is  
**[18:52]** >> um running within Claude code and the  
**[18:57]** the non-plugin like the the keep it  
**[19:00]** really simple is the idea  
**[19:03]** >> of an orchestrator running chord code.  
**[19:06]** So or running a harness.  
**[19:09]** >> So you have the outer harness and then  
**[19:10]** the inner harness, right?  
**[19:12]** >> This is the idea of between the inner  
**[19:13]** harness and the outer harness. So  
**[19:15]** remember I said opus is forgetful the  
**[19:17]** current opus is forgetful for example  
**[19:20]** when I'm doing loom and building loom I  
**[19:23]** see that always forgets translations  
**[19:26]** >> so cool you got this raph loop to do  
**[19:29]** what it's meant to do you got a  
**[19:31]** supervisor on top which sees if it did  
**[19:34]** asks if it did translations and if the  
**[19:36]** translations don't work you run another  
**[19:38]** Ralph loop to nudge it hey did you do  
**[19:40]** translations so the idea behind Ralph is  
**[19:43]** an outer layer orchestrator,  
**[19:46]** not a in a loop.  
**[19:48]** >> So it doesn't it doesn't just have to be  
**[19:51]** loop and do it forever. Your loop could  
**[19:53]** actually have like, you know, run  
**[19:55]** the main prompt  
**[19:57]** >> and then you could have another one  
**[19:59]** which is like  
**[20:01]** classify if X was done.  
**[20:04]** >> Correct. We'reing  
**[20:06]** >> jump out to other prompts like add the  
**[20:08]** tests and fix the tests or like do the  
**[20:11]** translations or whatever it is. Yeah,  
**[20:13]** we're engineering into places that don't  
**[20:15]** even have names for these concepts yet.  
**[20:18]** D. [laughter]  
**[20:19]** >> Yeah, you can front Antropic on this  
**[20:22]** one.  
**[20:23]** >> Yeah. What do you want to I So I was  
**[20:25]** thinking uh there was some conversation  
**[20:27]** on Twitter which was like okay if cloud  
**[20:29]** code is the harness what is the name you  
**[20:31]** give for engineering the slash commands  
**[20:34]** and plugins and cloud code and prompts  
**[20:36]** and maybe the bash loop that you wrap  
**[20:38]** around it because like you could say  
**[20:39]** that the Ralph loop script is becomes  
**[20:42]** part of the harness and you've created a  
**[20:44]** new harness on the building block that  
**[20:46]** is cla code or amp or open code or  
**[20:48]** whatever but someone else posted is like  
**[20:50]** well if if cla code is the harness if  
**[20:53]** the if the coding model agent CLI tool  
**[20:55]** is the harness, then the things you  
**[20:57]** build to control it are the res. And so  
**[21:00]** now I'm like, what about what is reins  
**[21:02]** engineering? But I I hope that one  
**[21:04]** doesn't catch on because it sounds  
**[21:05]** really dumb.  
**[21:05]** >> No, no, I have some ideas. I spicy. It's  
**[21:10]** called software engineering.  
**[21:12]** >> It's called software engineering.  
**[21:14]** >> So  
**[21:14]** >> I like it. We need the new term because  
**[21:18]** um there are so many people who just  
**[21:21]** don't get it right now and in denialism  
**[21:23]** that this is good. They're in their cope  
**[21:25]** land and people want a way to  
**[21:27]** differentiate  
**[21:28]** >> to they want to different differentiate  
**[21:31]** their skills. Like we had like  
**[21:33]** admins and devops and sres they created  
**[21:36]** these new titles to diff differentiate  
**[21:38]** and eventually those titles got muddied.  
**[21:41]** >> Yep. Um  
**[21:43]** cuz people will go, "Oh, I'm I'm DevOps  
**[21:45]** now cuz I know Kubernetes. Oh, I am I'm  
**[21:48]** an AI engineer now because I know like  
**[21:51]** like how to malic the array um or how  
**[21:55]** the inferencing loop works." No, no.  
**[21:57]** These are just fundamental new skills.  
**[21:59]** And if you don't have what we're talking  
**[22:01]** about in a year, I think it's going to  
**[22:03]** be really rough in the employment market  
**[22:06]** for high performance companies. Like  
**[22:08]** I've already seen things at like fangish  
**[22:11]** companies. Won't go into specifics  
**[22:13]** because we're live, but like like if  
**[22:16]** you're a software engineering manager  
**[22:18]** right now, um axes are coming out like  
**[22:22]** they want your team, which you have no  
**[22:24]** control over really  
**[22:27]** >> because there humans to get good at AI.  
**[22:32]** >> Um so it's kind of got to be kind of  
**[22:33]** brutal. It's kind of kind of brutal.  
**[22:35]** Like everyone wants people to get good  
**[22:37]** at AI, but really comes down to if  
**[22:39]** someone's curious or not. Really? Did  
**[22:41]** you make the the right hire originally?  
**[22:44]** >> Yep.  
**[22:46]** >> Um,  
**[22:47]** >> so I think it's software engineering,  
**[22:48]** Dex.  
**[22:49]** >> I think it's just literally software  
**[22:51]** engineering, but what it means to be  
**[22:52]** software engineer changes.  
**[22:55]** >> I did realize that um  
**[23:00]** I think we can get push. I just want to  
**[23:02]** make sure that we're allowed to commit  
**[23:04]** because I know you have to do some uh  
**[23:07]** >> yeah Golf login  
**[23:09]** >> the so the G so I have deploy keys on  
**[23:11]** both these boxes. Um  
**[23:14]** >> let's see if we can I'm like T-Mox  
**[23:17]** within T-Mox is cra I'm really lucky I  
**[23:19]** changed my default T-m prefix. So now I  
**[23:22]** but I have to remember what the default  
**[23:23]** one is on the new on the new boxes.  
**[23:27]** >> Um  
**[23:28]** >> we're on a tangent folks.  
**[23:29]** >> Yeah. Um, you should be thinking about  
**[23:31]** loop backs. Um, any way that you that  
**[23:36]** the LLM can automatically scrape uh  
**[23:39]** context. So the LLM's know how to drive  
**[23:42]** t-mucks. So instead of doing some  
**[23:44]** background clawed code agent, etc. Just  
**[23:47]** tell it to spawn a T-max session, split  
**[23:49]** the pain and scrape the pain. It does it  
**[23:51]** really well. If you got like a web  
**[23:53]** server log and then a backend API log  
**[23:56]** created in two like in two splits. Um,  
**[24:00]** and just tell Claude or the model to go  
**[24:03]** grab the pain and then you got automatic  
**[24:05]** loop back for troubleshooting. And this  
**[24:07]** you don't need to be in the loop. You're  
**[24:10]** on the loop and you're programming the  
**[24:11]** loop. And this is all Ralph.  
**[24:18]** Um, yes. Uh we actually did on last week  
**[24:22]** uh a couple weeks ago on AI that works  
**[24:23]** we did do a we did a session on git work  
**[24:25]** trees and we figured out that uh we did  
**[24:29]** some demos of like having one Ralph  
**[24:31]** running over here and using T-M not  
**[24:33]** route but having one claude running over  
**[24:34]** here and using T-Mox to like scrape the  
**[24:37]** pains of the other ones and then like  
**[24:39]** merge in the results from the work trees  
**[24:41]** and resolve the conflicts.  
**[24:43]** >> Yeah. Well, whilst that kicks off, we're  
**[24:46]** also on another tangent. This is a  
**[24:48]** concept that you coined.  
**[24:50]** >> Um,  
**[24:51]** >> damn it. Because I just didn't write it.  
**[24:54]** You You me. Um,  
**[24:57]** >> that's why I invite you on my streams. I  
**[24:59]** want you to come up with fun words and I  
**[25:00]** I'll just be there while you do it,  
**[25:02]** which is  
**[25:03]** >> most recording what happened anyways.  
**[25:05]** >> Most test runners are trash. They output  
**[25:08]** too many tokens. You only want to output  
**[25:09]** the failing test case.  
**[25:11]** >> Oh, I wrote a blog post on this. Did you  
**[25:13]** see this?  
**[25:13]** >> I did. And it's it's golden, Derek. It's  
**[25:16]** golden. Most runners are are trash.  
**[25:20]** >> This is actually based on a bunch of  
**[25:21]** work that I think the first person to  
**[25:23]** write this stuff in our codebase was  
**[25:25]** when um Allison was hacking. Like this  
**[25:28]** is a version of a script that like  
**[25:30]** Allison and Claude built a while ago  
**[25:32]** because it was just like why would you  
**[25:34]** want to output like a million tokens of  
**[25:37]** like go spew like JSON test output if  
**[25:40]** the test is passing?  
**[25:42]** What happens is normally the test run  
**[25:44]** the output's so large what it does is it  
**[25:46]** goes tail minus 100 but if the error is  
**[25:49]** at the top the tail it misses the tail.  
**[25:53]** >> Yeah. No, this is the thing that  
**[25:54]** happened all the time where it's uh  
**[25:56]** yeah, it's just head-N50 and then yeah,  
**[25:58]** if your tests take 30 seconds then  
**[26:00]** you're fine. But most people that we  
**[26:01]** work with are like teams with 50,  
**[26:03]** hundred, thousands of engineers and  
**[26:05]** their test suites if you run them wrong,  
**[26:06]** they can take hours. And so like there's  
**[26:09]** some work to be done to like  
**[26:12]** if it runs the head and then something  
**[26:14]** fails but it doesn't see it and then it  
**[26:15]** has to run it again, it's like that's  
**[26:16]** not wasted tokens. It is wasted tokens  
**[26:19]** and it is wasted time. But like if in  
**[26:21]** most cases most people aren't doing this  
**[26:23]** super hands-off Ralph Wigum thing. And  
**[26:25]** so what just happened is I finished my  
**[26:27]** code and I the human am sitting there  
**[26:29]** waiting for it to run this fiveminute  
**[26:30]** test suite again.  
**[26:31]** >> That's the key. And I'm like why would I  
**[26:33]** ever use this tool?  
**[26:35]** >> That's a that's the key like I'm not in  
**[26:38]** the loop bashing the the array and  
**[26:41]** manually allocate it and like ste trying  
**[26:43]** to steer it like most people use cursor.  
**[26:46]** Instead, I I try to oneshot it at the  
**[26:49]** top and then I watch it and then if you  
**[26:52]** watch it enough, you notice stupid  
**[26:53]** patterns and then you make discoveries  
**[26:55]** like the testr runner thing that you  
**[26:57]** just showed.  
**[26:58]** >> Yep.  
**[26:59]** >> And you go, "Oh, that's a trick that  
**[27:01]** works.  
**[27:04]** >> I've also I've also  
**[27:05]** >> discoveries are found by treating clawed  
**[27:08]** code as a fireplace."  
**[27:11]** >> as a fireplace that you just watch.  
**[27:14]** >> You just sit there and watch it. you  
**[27:16]** like you're out camping. You're sitting  
**[27:17]** sitting there watching the fire going.  
**[27:19]** >> I actually I had a I had a party on uh  
**[27:22]** Tuesday, a little like pre-New New  
**[27:23]** Year's event and I wanted to set this up  
**[27:26]** and I just didn't have time. But I  
**[27:27]** really wanted to have one of the  
**[27:29]** attractions at the party is a uh laptop  
**[27:33]** hooked up to the TV and one there's a  
**[27:36]** terminal in a web app and you can see  
**[27:37]** Ralph working and then anyone at the  
**[27:39]** party can go up and edit the specs and  
**[27:41]** like control the trajectory of the loop.  
**[27:45]** Uh, so next time you come to one of my  
**[27:46]** parties, we'll have we'll have that.  
**[27:49]** >> Mate, I've still got a couple  
**[27:50]** pre-planned trips, so it's just a matter  
**[27:52]** of when I come to SF.  
**[27:54]** >> Okay. When you come to SF, we're doing  
**[27:56]** we're doing a Cursed Lang hackathon.  
**[27:59]** We could probably also do a Ralph plus  
**[28:00]** Cursed Lang hackathon. I think that  
**[28:02]** would be really, really fun. Uh,  
**[28:05]** >> and yeah, just like how do you make this  
**[28:06]** it's it's deeply technical and you can  
**[28:08]** change the world. you could build  
**[28:09]** incredibly useful things that actually  
**[28:11]** make many people's lives better, but  
**[28:13]** also just like the perspective of like  
**[28:16]** some of this is just art and like  
**[28:18]** >> how do you how do you bridge the gap  
**[28:20]** between art and and and utility and  
**[28:22]** yeah, it's a fun time.  
**[28:24]** >> Yeah, it's it's a crazy time. So, I'm  
**[28:26]** down for that. Um,  
**[28:28]** let me get Loom done because I think  
**[28:31]** Loom is the encapsulation of some of  
**[28:33]** these ideas into  
**[28:36]** uh, essentially what is a remote  
**[28:39]** ephemeral sandbox coding harness. M  
**[28:42]** >> so the ability for a self-hosted  
**[28:46]** platform to actually create its own uh  
**[28:49]** remote agents weavers and then it's just  
**[28:53]** like your standard uh like agentic  
**[28:56]** harness which is 300 lines of code. If  
**[28:59]** people think claude code's amazing, it's  
**[29:01]** not. It's literally the model that does  
**[29:03]** all the work. Go look at my how to build  
**[29:06]** an a how to build an agent harness. All  
**[29:10]** right. So you got this harness, you got  
**[29:13]** this remote like provisioner on  
**[29:15]** infrastructure.  
**[29:17]** >> The next step there is really like how  
**[29:20]** do you like how could you encodify Ralph  
**[29:25]** and like little these all these nudges  
**[29:27]** and all these pokes and what happens if  
**[29:29]** it's a source control? It's also source  
**[29:32]** control. Like I I've been wanting to get  
**[29:34]** off GitHub for a long time and evolves  
**[29:36]** SCM.  
**[29:37]** >> Did you build your own now?  
**[29:39]** >> Yeah. the last three days like AFK I now  
**[29:43]** have a remote provisioner I now have  
**[29:46]** full like Aback device login flows OF  
**[29:50]** login flows tailwind UI  
**[29:54]** uh it's got full SCM hosting full SCM  
**[29:57]** mirroring we've got a harness so I've  
**[29:59]** got the CLI now that can like spawn  
**[30:02]** remote infrastructure  
**[30:05]** kick kick off an agent and then when it  
**[30:07]** says that it thinks that it's done then  
**[30:08]** then I can set up this like almost  
**[30:10]** [snorts] like a pix chain reaction of  
**[30:13]** agent pokes agent. So this is like do  
**[30:16]** did you do the translation do all these  
**[30:18]** things and  
**[30:20]** >> if you control the entire stack  
**[30:22]** >> from source code you can modify and  
**[30:25]** change that stack to your needs includes  
**[30:28]** like source control as like a memory for  
**[30:31]** agents.  
**[30:33]** >> I love it. Um, I've realized one other  
**[30:37]** thing here, which is that I did not put  
**[30:39]** a push command in my prompt, and so the  
**[30:41]** agents didn't push their stuff.  
**[30:44]** >> Yeah. So, that's that's another thing we  
**[30:47]** haven't covered off yet is the idea of  
**[30:50]** if you have a a shell script on the  
**[30:53]** outside or an orchestrator over the  
**[30:56]** harness,  
**[30:58]** >> that's true, you could just do the push  
**[30:59]** in the orchestrator,  
**[31:00]** >> correct? which makes it deterministic.  
**[31:02]** But you can also add deterministic push,  
**[31:04]** deterministic commit. You could add uh  
**[31:07]** deterministic  
**[31:09]** like evaluation whether it meets your  
**[31:12]** criteria. Does it do a git reset hard?  
**[31:14]** Does it run Ralph further on what you've  
**[31:17]** already got? Does it bake it more or  
**[31:19]** does it just reset and try again?  
**[31:21]** >> Yeah.  
**[31:22]** >> But if you run  
**[31:23]** >> I like the communist. You're just gonna  
**[31:25]** get you're just gonna get like steak  
**[31:27]** that's either blue or it's charred.  
**[31:33]** >> Okay. So, here's what's interesting is  
**[31:35]** we are back to non-determinism. So, you  
**[31:37]** see this one over here started running  
**[31:40]** the thing and it actually emitted the  
**[31:41]** promise because it read the prompt and  
**[31:44]** it said, "Okay, everything is done with  
**[31:46]** the first thing like it. It finished the  
**[31:49]** prompt and it did the first thing, but  
**[31:51]** it's now not looping."  
**[31:53]** >> And so, Uh yeah,  
**[31:55]** >> like if I tell you not to think about an  
**[31:57]** elephant, what are you thinking about,  
**[31:58]** Dex?  
**[31:59]** >> Elephants.  
**[32:01]** >> Exactly. Like this is another thing  
**[32:04]** about prompt engineering. Like people  
**[32:05]** go, it's important that you do not  
**[32:08]** >> do XYZ,  
**[32:10]** >> right? And next thing you know, it's in  
**[32:11]** the context window. I'm going to think  
**[32:13]** about XYZ. And it forgets the important  
**[32:15]** not.  
**[32:17]** >> The less that's in that context window,  
**[32:20]** the better your outcomes.  
**[32:22]** That includes trying to treat it like a  
**[32:25]** little kid.  
**[32:30]** >> So, I want to actually edit this because  
**[32:32]** I haven't worked with this plugin much.  
**[32:34]** So, it's like a little bit of this is my  
**[32:37]** uh  
**[32:40]** huh.  
**[32:42]** Uh,  
**[32:44]** a little bit of this is my um like just  
**[32:47]** learning the the tricks of these of this  
**[32:49]** plugin. But it looks like the Ralph loop  
**[32:51]** is finished.  
**[32:52]** So, I'm going to make another one.  
**[32:56]** Um,  
**[32:58]** down.  
**[33:02]** Let's see.  
**[33:13]** Or what is it? Completion promise. I'm  
**[33:15]** just going to try to run it without a  
**[33:16]** completion promise and see if this will  
**[33:18]** just run forever. Yeah,  
**[33:21]** >> I hope uh people stumb upon this video  
**[33:23]** and they um they're able to disconnect  
**[33:26]** the two between like the official  
**[33:30]** product implementation and go, "Oh, wow.  
**[33:32]** It's bienthanropic."  
**[33:34]** Verse  
**[33:35]** uh learning the fundamentals  
**[33:38]** of like  
**[33:39]** >> of like why it works and why it's good,  
**[33:41]** >> why it works and how does it work and  
**[33:43]** like actually watching it. Like I have  
**[33:45]** AFKed it for 3 months, but I wasn't  
**[33:48]** paying for tokens. I saw it rewrite the  
**[33:50]** Lexa and Pasa like  
**[33:54]** so many times. And I thought the model  
**[33:57]** was the issue. It wasn't the model.  
**[34:00]** >> Hey Dex, do you know someone who uh said  
**[34:02]** that you should spend some time reading  
**[34:04]** the specs and like more time on the spec  
**[34:07]** because one bad spec equals  
**[34:10]** uh like one [laughter] bad line of code  
**[34:12]** is one bad line of code. one bad spec is  
**[34:14]** like 10 new product features, 10,000  
**[34:17]** lines of like crap and junk because in  
**[34:20]** the case of cursed,  
**[34:22]** >> yeah, in the case of cursed, my spec was  
**[34:26]** wrong. So, it was tearing down the Lexa  
**[34:28]** and the pasa like  
**[34:31]** >> because I declared the same keyword for  
**[34:36]** and and or to be the same keyword.  
**[34:39]** >> Oh, because you had a mistake in your in  
**[34:41]** the list. You couldn't come up I was  
**[34:43]** saying that the model was bad and loot.  
**[34:45]** It was literally garbage in, garbage  
**[34:48]** out. Like, you got to eyeball these. You  
**[34:50]** >> didn't know enough. You didn't know  
**[34:51]** enough Gen Z slang to do a good job.  
**[34:54]** >> Yeah. And I've never met a compiler  
**[34:56]** before.  
**[34:56]** >> Keywords.  
**[34:58]** >> I ran out of gen.  
**[35:00]** >> I'm just going to show this real quick  
**[35:01]** for people who are not familiar, but  
**[35:03]** this is a programming language that was  
**[35:05]** built with Ralph uh three times over in  
**[35:07]** three different it was C and then Rust  
**[35:09]** and then Zigg, right?  
**[35:10]** >> Yeah. playing with the notion of back  
**[35:12]** pressure and what like what's in the  
**[35:14]** training data sets and all that stuff.  
**[35:18]** >> Yeah, this is cool. Um, anyways, I'm I'm  
**[35:21]** going to leave this running for a while.  
**[35:22]** I'm probably not going to be sitting  
**[35:23]** here, but I hope if you're watching, uh,  
**[35:25]** you had fun and you learned some stuff.  
**[35:27]** And Jeeoff, I know you got to head into  
**[35:28]** work in a minute.  
**[35:29]** >> I got to head into work.  
**[35:30]** >> Any any final thoughts? Any last words?  
**[35:32]** I mean, you kind of said your advice,  
**[35:34]** which is like don't just jump on the  
**[35:36]** plugin and the name and the cartoon  
**[35:38]** character, but like actually it's it's  
**[35:40]** kind of as much of anything as a  
**[35:41]** teaching tool and like go learn why it  
**[35:43]** works and why it was designed the way it  
**[35:45]** was.  
**[35:45]** >> Yeah. Think like a think like a C or C++  
**[35:48]** engineer. Think that you got this array.  
**[35:50]** There's no memory on the server side.  
**[35:52]** You it's a sliding window over the  
**[35:55]** array. You want to set only one goal and  
**[35:58]** objective in that array. And um you want  
**[36:02]** to leave some like uh head room if  
**[36:05]** you're  
**[36:06]** >> Mhm.  
**[36:06]** >> if you're not complete AFKing, you want  
**[36:08]** to leave some headroom because sometimes  
**[36:10]** you got this beautiful context window  
**[36:11]** that you just fall in love with  
**[36:13]** >> and then you're like, "Oh, can I squeeze  
**[36:15]** some bore out? Maybe it's not a new  
**[36:17]** loop. Maybe like like you get just you  
**[36:19]** get these golden windows."  
**[36:21]** >> Um  
**[36:22]** >> yeah. Where it's like the trajectory is  
**[36:23]** perfect and it's running the test  
**[36:25]** properly and you get in the right place.  
**[36:26]** >> You want to save it. You want to save  
**[36:28]** it. Like that's something I think that  
**[36:31]** we as an area of research uh in agenic  
**[36:34]** harnesses is like the ability to say  
**[36:38]** this is the perfect context when I want  
**[36:40]** to go back to it.  
**[36:44]** >> Deliberate malicking.  
**[36:45]** >> Yeah, deliberate malicking. Um and less  
**[36:49]** is more.  
**[36:51]** >> Holy crap. Um take your claw code rules  
**[36:54]** and tokenize them.  
**[36:57]** [laughter]  
**[36:58]** Go to like Tik Tok get tick token off  
**[37:00]** GitHub. Run it through the tokenizer or  
**[37:02]** the open AI tokenizer.  
**[37:04]** >> Read the harness guides.  
**[37:09]** Um, read the harness guides. Like  
**[37:12]** anthropic says it's important to shout  
**[37:14]** at the LLM. GPT5 says if you shout at  
**[37:18]** it, it becomes timid.  
**[37:19]** >> You dune the model. Yeah. It stops being  
**[37:22]** >> Yeah, you can look at the look at the  
**[37:23]** tokenizer. I mean this is easy because  
**[37:25]** it's this but like yeah we talk about  
**[37:26]** this all the time as if like you should  
**[37:28]** go look at how the model sees what you  
**[37:30]** say because when you type JSON into here  
**[37:32]** you see like there are so many extra  
**[37:34]** charact like this is way denser than  
**[37:36]** just feeding the model words and so you  
**[37:38]** should turn the JSON deterministically  
**[37:40]** turn it into words or XML or something  
**[37:42]** more token efficient.  
**[37:44]** >> Yeah, I'll leave you with a quip.  
**[37:46]** >> Yeah, let's go.  
**[37:48]** So  
**[37:50]** you could only fit about a  
**[37:53]** actually maybe here's the quip.  
**[37:56]** I remember someone coming to me and  
**[37:59]** wanting to do an analysis on some data  
**[38:01]** using our labs.  
**[38:03]** >> Mhm.  
**[38:03]** >> And I go, "How big is the data set?" And  
**[38:05]** that that person went, "Oh, it's small.  
**[38:07]** It's only a terabyte."  
**[38:10]** So I had to pull up the chair. had to  
**[38:12]** pull up the chair and go, "Oh, this is  
**[38:15]** only a Commodore 64  
**[38:18]** worth of memory." So, if you want to  
**[38:21]** know how big like 200k of tokens is, um,  
**[38:26]** you got you've got it's tiny. You've got  
**[38:28]** like a the model gets about a 16k token  
**[38:32]** overhead.  
**[38:34]** >> The harness gets about a 16k overhead.  
**[38:36]** you only got about 176K usable, not the  
**[38:39]** full 200 because there's overheads,  
**[38:42]** >> right? There's the there's the system  
**[38:43]** messages that come in, right?  
**[38:45]** >> Yeah. Yeah. Yeah. So, for that person, I  
**[38:50]** u downloaded Star Wars Episode 1 movie  
**[38:54]** script. [snorts]  
**[38:55]** >> Mhm.  
**[38:55]** >> And I tokenized it.  
**[38:57]** >> Okay.  
**[38:58]** >> And that that worked out to be about 60K  
**[39:01]** of tokens or about 136 KB on disk.  
**[39:05]** You can only fit two movie the max of  
**[39:08]** one movie or two movies into the context  
**[39:10]** window.  
**[39:12]** >> Here's the new measurement. H how many  
**[39:14]** movies can you fit into the to get  
**[39:16]** people thinking about like visually from  
**[39:21]** like when we talk about tokens it's it's  
**[39:24]** just this weird concept like you can  
**[39:27]** only fit about 136 KB and people go  
**[39:29]** what's 136 KB it's Star Wars movie  
**[39:31]** script  
**[39:36]** >> amazing  
**[39:37]** >> that that includes the tool output if  
**[39:40]** you and if you apply the domain back  
**[39:41]** that includes your tool output, your  
**[39:43]** spec allocation, it includes your  
**[39:46]** initial prompts. It goes by fast.  
**[39:51]** Goes by fast.  
**[39:54]** >> Yeah,  
**[39:54]** >> Dex.  
**[39:55]** >> So, it's both you can do a ton, but it's  
**[39:56]** also it's it's incredibly small and uh  
**[39:59]** the engineering and being thoughtful  
**[40:01]** about how you use this stuff uh can make  
**[40:03]** a huge impact.  
**[40:04]** >> Correct. And your best learnings will  
**[40:06]** come by treating it like a Twitch stream  
**[40:08]** or sitting by the fireplace and then  
**[40:10]** asking the all these questions and  
**[40:12]** trying to figure out why it does certain  
**[40:14]** behaviors and there's no explainable  
**[40:17]** reason. But then you notice patterns and  
**[40:19]** then you you tune things  
**[40:22]** like your agents MD which should only be  
**[40:24]** about 60 lines of uh code by the way.  
**[40:28]** >> Yeah. Agents MD should be small.  
**[40:30]** Everything should be small. you want to  
**[40:32]** maximize  
**[40:33]** >> useful working time in the smart zone.  
**[40:36]** So, uh, this is super fun. I decided to  
**[40:38]** do this on as a as a bit and Jeff texted  
**[40:40]** me. I was like, I'm gonna come hang out  
**[40:41]** and talk about Ralph. I was like,  
**[40:43]** incredible. So, thank you so much for  
**[40:44]** joining. Uh,  
**[40:45]** >> anytime, mate.  
**[40:46]** >> Post a video somewhere. Uh, if you want  
**[40:48]** to do a recap or or a retrospective, I'm  
**[40:50]** I'm happy to dive deeper once this thing  
**[40:52]** is like cooked for a couple hours.  
**[40:55]** >> Peace. Until I'm next in San Fran, mate.  
**[40:57]** >> All right, sir. Enjoy. See you.  
**[41:06]** Okay, that was Jeff Huntley. I am now  
**[41:09]** going to uh get back to work. Uh and  
**[41:12]** we're going to let this thing cook and  
**[41:13]** we will just leave it online on the  
**[41:15]** stream for a bit. So, I'm going to turn  
**[41:18]** off the OBS camera. I'm gone now. And uh  
**[41:23]** yeah, enjoy. We'll check back in in a  
**[41:25]** little bit.  
**[41:27]** Cheers.  