# Transcript: https://www.youtube.com/watch?v=kQu5pWKS8GA

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 1372

---

**[00:00]** Let's solve the problem of Claude Code  
**[00:02]** and memory. Getting AI systems to  
**[00:04]** reliably and accurately answer questions  
**[00:07]** about past conversations or giant troves  
**[00:11]** of documents is a problem we have been  
**[00:13]** trying to solve for years and the  
**[00:15]** typical response has been rag, retrieval  
**[00:19]** augmented generation. And while this  
**[00:20]** video is titled the seven levels of  
**[00:22]** Claude Code and rag, what this video is  
**[00:25]** really about is deconstructing that  
**[00:27]** problem of Claude Code and really AI  
**[00:30]** systems in general and memory. And even  
**[00:33]** more importantly, this video is about  
**[00:34]** giving you a roadmap that shows you  
**[00:36]** where you stand in this fight between AI  
**[00:38]** systems and memory and what you can do  
**[00:41]** to get to the next level. So, as we  
**[00:43]** journey through these seven levels of  
**[00:45]** Claude Code and rag, we are going to hit  
**[00:46]** on a number of topics, but we are not  
**[00:48]** going to start here in graph rag or  
**[00:50]** anything complicated. We're going to  
**[00:52]** start at the beginning, which is just  
**[00:53]** the basic memory systems that are native  
**[00:56]** to Claude Code because, sad as it is to  
**[00:59]** say, this is where most people not only  
**[01:01]** begin, but it's where they stay. From  
**[01:03]** auto memory and things like Claude MD,  
**[01:05]** we're going to move to outside tools,  
**[01:06]** things like Obsidian before we  
**[01:09]** eventually find ourselves with the big  
**[01:11]** boys, with the true rag systems. At  
**[01:13]** these levels, we'll talk about what rag  
**[01:15]** actually is, how it works, the different  
**[01:17]** types of rag, naive rag versus graph rag  
**[01:20]** versus agentic rag, things like  
**[01:21]** rerankers and everything in between. And  
**[01:23]** at each level, we're going to break it  
**[01:24]** down in the same manner. We're going to  
**[01:26]** talk about what to expect at that level,  
**[01:28]** the skills you need to master, the traps  
**[01:30]** you need to avoid, and what you need to  
**[01:31]** do to move on to the follow-on level.  
**[01:34]** What this video will not be is a super  
**[01:36]** in-depth technical explanation of how to  
**[01:39]** necessarily set up these specific  
**[01:40]** systems because I've already done this  
**[01:42]** in many instances. When we talk about  
**[01:44]** graph rag and light rag, for example, or  
**[01:46]** even more advanced topics like rag  
**[01:49]** anything in these different sort of  
**[01:50]** embedding systems, I've done videos  
**[01:52]** where I break down from the very  
**[01:54]** beginning to the very end how to set  
**[01:55]** that up yourself. So, when we get to  
**[01:56]** those sections, I will link those videos  
**[01:59]** and this is for both our sake so this  
**[02:01]** video isn't 5 hours long, but for those  
**[02:03]** levels, we're still going to talk about  
**[02:05]** what that actually means, what each  
**[02:07]** system buys you, and when you should be  
**[02:08]** using it. But before we start with level  
**[02:10]** one, a quick word from today's sponsor,  
**[02:13]** me. So, just last month, I released the  
**[02:15]** Claude Code Masterclass and is the  
**[02:16]** number one way to go from zero to AI  
**[02:19]** dev, especially if you don't come from a  
**[02:21]** technical background. And this  
**[02:22]** Masterclass is a little bit different  
**[02:24]** because we focus on a number of  
**[02:26]** different use cases to learn how to use  
**[02:28]** Claude Code. One of those is something  
**[02:30]** like production level rag, how to build  
**[02:32]** the rag systems you're going to see in  
**[02:34]** this video in a real-life scenario and  
**[02:37]** actually use it as a member of a team or  
**[02:39]** sell it to a client. That's the kind of  
**[02:41]** stuff we focus on. So, if you want to  
**[02:43]** get access, you can find it inside of  
**[02:44]** Chase AI Plus. There's a link to that in  
**[02:46]** the pinned comment and we'd love to have  
**[02:48]** you there. So, now let's start with  
**[02:49]** level one and that's auto memory. These  
**[02:52]** are the systems that Claude Code  
**[02:53]** automatically uses to create some sort  
**[02:56]** of memory apparatus, to actually  
**[02:58]** remember things that you've talked  
**[02:59]** about. And you know you're here if  
**[03:01]** you've never set anything up  
**[03:03]** intentionally to help Claude Code  
**[03:06]** remember context in general about  
**[03:07]** previous conversations or just stuff  
**[03:10]** that's going on in your codebase. And  
**[03:11]** when we talk about auto memory, that is  
**[03:13]** quite literally what it is called, the  
**[03:15]** auto memory system, which is  
**[03:16]** automatically enabled when you use  
**[03:18]** Claude Code, essentially allows Claude  
**[03:21]** Code to create markdown files on its own  
**[03:24]** that sort of list out things it thinks  
**[03:27]** are important about you and that  
**[03:29]** particular project. And this is purely  
**[03:31]** based off of its own intuition based on  
**[03:34]** your conversations. And I can see these  
**[03:35]** memory files it's created again, it does  
**[03:37]** this on its own. If you go into your dot  
**[03:39]** Claude folder, you go into projects, you  
**[03:41]** will see a folder there that is called  
**[03:43]** memory. And inside that file, you will  
**[03:45]** see a number of markdown files. Here,  
**[03:47]** there are four of them and they're like  
**[03:48]** Claude Code's version of posted notes  
**[03:50]** saying, "Oh yeah, he mentioned this one  
**[03:52]** time about his YouTube project growth  
**[03:55]** goals. Let's write that down." And  
**[03:57]** inside of everyone's memory folder,  
**[03:59]** there will be a memory.md file. So, you  
**[04:02]** see in this memory file, it has a little  
**[04:03]** note about one of my skills and then it  
**[04:05]** has, you know, essentially an index of  
**[04:07]** all these sub memory files saying, "Hey,  
**[04:09]** there's a YouTube growth one in here, a  
**[04:10]** revenue one, a references one, and  
**[04:12]** here's what's inside of it." So, if I'm  
**[04:14]** just talking to Claude Code in my vault  
**[04:16]** file and I mention something about  
**[04:18]** YouTube and sort of my goals with growth  
**[04:20]** or whatever, it's going to reference  
**[04:22]** this and say, "Oh yeah, Chase is trying  
**[04:23]** to get, you know, X amount of  
**[04:24]** subscribers by the end of 2026."  
**[04:27]** It's cute, but ultimately it's not that  
**[04:30]** useful. It's kind of like when you're  
**[04:31]** inside of ChatGPT and it will bring up  
**[04:33]** random stuff about previous  
**[04:35]** conversations and it almost like  
**[04:37]** shoehorns it in. It's like, "Okay, I get  
**[04:39]** it. You remembered this, but I don't  
**[04:41]** really care." And honestly, it's a  
**[04:42]** little weird you keep bringing that up.  
**[04:43]** I prefer if you didn't. And  
**[04:44]** unfortunately, this is where most people  
**[04:46]** stay in their memory journey and it's  
**[04:48]** built upon a somewhat almost abusive  
**[04:50]** past that we all have when it comes to  
**[04:52]** using these chatbots because these  
**[04:54]** chatbots don't have  
**[04:56]** any sort of real memory from  
**[04:58]** conversation to conversation and so  
**[05:00]** we're always scared to death of having  
**[05:03]** to exit out of a chat window or exit out  
**[05:05]** of a terminal session because you think,  
**[05:07]** "Oh my gosh, it's not going to remember  
**[05:08]** my conversation." And this is actually a  
**[05:10]** real problem because what is everybody's  
**[05:12]** answer to  
**[05:14]** the chat window  
**[05:16]** not being able to remember anything?  
**[05:17]** Well, the answer is you just keep that  
**[05:19]** conversation going forever because you  
**[05:21]** don't want to get to a scenario where  
**[05:23]** you have to exit out and it forgets  
**[05:24]** everything. This is a fear that is born  
**[05:26]** here inside of these chat windows,  
**[05:27]** beginning with ChatGPT and same thing  
**[05:29]** with Claude's web app. And honestly,  
**[05:31]** used to be infinitely worse with  
**[05:32]** Claude's web app because I think we all  
**[05:33]** remember before the days of the 1  
**[05:35]** million context window where you would  
**[05:36]** have like 30 minutes to talk with Claude  
**[05:38]** and be like, "Well, see you in 4 hours."  
**[05:40]** The issue is people have brought that  
**[05:41]** sort of  
**[05:43]** psychotic, neurotic behavior to the  
**[05:45]** terminal and what they do, in large part  
**[05:48]** because you now can get away with it  
**[05:49]** with a 1 million context window, is they  
**[05:51]** never clear. They just keep talking and  
**[05:53]** talking and talking with Claude Code  
**[05:55]** because they never want it to forget  
**[05:56]** what they're talking about because of  
**[05:58]** these memory problems. And the issue  
**[06:00]** with that is your efficiency goes way  
**[06:02]** down over time the more you talk with  
**[06:04]** Claude Code inside of the same session.  
**[06:06]** And this is the fundamental idea of  
**[06:08]** context rot. If you don't know what  
**[06:09]** context rot is,  
**[06:11]** it's the phenomena that the more I use  
**[06:14]** an AI system within its same session,  
**[06:16]** within its same chat, and I fill up that  
**[06:17]** context window, the worse it gets. You  
**[06:19]** can see that right here. Claude Code 1  
**[06:22]** million context window at 256k tokens,  
**[06:26]** aka I've only filled up about a quarter  
**[06:28]** of its context window, we're at 92%. By  
**[06:32]** the end of it, 78. So, the more you use  
**[06:34]** it in the same chat, the worse it gets.  
**[06:36]** And that's one of the primary issues  
**[06:37]** people have with AI systems and memory.  
**[06:39]** I have Claude Code. It has a million  
**[06:42]** context now and yet I do not want it to  
**[06:44]** forget about the conversation I'm  
**[06:45]** having. So, I just never exit the  
**[06:47]** window. I just fill it up and fill it up  
**[06:48]** and fill it up and two things happen.  
**[06:50]** One, effectiveness goes down like you  
**[06:52]** just saw. Two, your usage fills up a ton  
**[06:56]** because the amount of tokens that are  
**[06:58]** used at 1 million, at 800,000, you know,  
**[07:02]** context is way more than an 80,000  
**[07:05]** context. So,  
**[07:07]** this isn't the only issue, but kind of  
**[07:08]** off topic, we're in a current ecosystem  
**[07:10]** where everyone complains about Claude  
**[07:12]** Code being nerfed and my usage just gets  
**[07:14]** run up automatically. There's a number  
**[07:15]** of reasons for that, but one of them  
**[07:18]** undoubtedly is the fact that since 1  
**[07:20]** million context got introduced, people  
**[07:23]** have no clue how to manage their own  
**[07:24]** context window and they aren't nearly  
**[07:27]** they aren't nearly as aggressive with  
**[07:29]** clearing and resetting the conversation  
**[07:31]** as often as they should. But that's kind  
**[07:33]** of off topic. The point of that whole  
**[07:35]** discussion is that when it comes to  
**[07:37]** memory in this discussion about rag and  
**[07:40]** Claude Code, we have to keep context rot  
**[07:42]** in the back of our mind because we're  
**[07:43]** constantly trying to deal with this  
**[07:45]** tension of, "Okay, I want to ingest  
**[07:47]** context so Claude Code can answer  
**[07:49]** questions about a number of things, yet  
**[07:51]** at the same time, I don't want the  
**[07:52]** context to get too large because then  
**[07:55]** it's worse."  
**[07:56]** So, we just that always needs to be  
**[07:59]** something we're thinking about in this  
**[08:00]** conversation about memory. But to bring  
**[08:02]** this back to the actual video and level  
**[08:05]** one, what are people doing at level one?  
**[08:06]** The answer is they're not really doing  
**[08:07]** anything. And because they're not doing  
**[08:09]** anything, they just rely on a bloated  
**[08:11]** context window to remember things. So,  
**[08:13]** you know you're here when you've never  
**[08:15]** edited a Claude.md file and you've never  
**[08:17]** created any sort of artifact or any sort  
**[08:21]** of file that allows Claude Code to  
**[08:23]** realize what the heck is going on, what  
**[08:25]** it's actually done in the past, and what  
**[08:27]** it needs to do in the future. So, what  
**[08:28]** do we need to master at this level?  
**[08:30]** Well, really all you really need to  
**[08:31]** master, despite everything I wrote here,  
**[08:32]** is you just need to understand that auto  
**[08:34]** memory isn't enough and we need to take  
**[08:36]** an active role when it comes to Claude  
**[08:37]** Code and memory. Because the trap at  
**[08:39]** this level, if you don't take an active  
**[08:41]** role, you you have no control and we  
**[08:43]** need to control what Claude Code  
**[08:44]** considers when it answers our questions.  
**[08:46]** And so, to unlock level one and move on  
**[08:49]** to level two, we need memory that's  
**[08:52]** explicit and we need to figure out how  
**[08:55]** to actually do that. What files do you  
**[08:57]** need to edit and understand that they  
**[08:58]** even exist in order to take an active  
**[09:01]** role in this relationship. Now, level  
**[09:02]** two is all about one specific file and  
**[09:04]** that is the Claude.md file. When you  
**[09:06]** learn about this thing, it feels like a  
**[09:07]** godsend. Finally, there is a single  
**[09:10]** place where I can tell Claude Code some  
**[09:12]** rules and conventions that I always want  
**[09:14]** it to follow and it's going to do it.  
**[09:16]** And in fact, I can include things that I  
**[09:18]** want it to remember and it always will.  
**[09:19]** And it definitely feels like progress at  
**[09:21]** first. So, here's a template of a  
**[09:23]** standard Claude.md file for a personal  
**[09:27]** assistant project. Now, Claude Code's  
**[09:29]** going to automatically create a  
**[09:30]** Claude.md file, but you have the ability  
**[09:32]** to edit this or even update it on demand  
**[09:35]** by using a command like {slash} init.  
**[09:38]** And the idea of this thing is is it is  
**[09:40]** again like the holy grail of  
**[09:42]** instructions for Claude Code for that  
**[09:43]** particular project. For all intents and  
**[09:45]** purposes, Claude Code is going to take a  
**[09:47]** look at this before any task it  
**[09:50]** executes. So, if you want it to remember  
**[09:52]** specific things, what are you going to  
**[09:53]** do? You're going to put it in the  
**[09:54]** Claude.md,  
**[09:56]** theoretically. It's a bit of smaller  
**[09:58]** scale than something like rag, you know,  
**[10:00]** we aren't putting in, you know, complete  
**[10:02]** documents in here, but it's things you  
**[10:04]** want Claude code to always remember and  
**[10:06]** conventions you want it to follow. So  
**[10:07]** for this one, we have an about me  
**[10:09]** section, we have a breakdown of the  
**[10:10]** structure of the file system and how we  
**[10:12]** want it to actually operate when we give  
**[10:14]** it commands. And like I said, because  
**[10:16]** this is referenced on essentially every  
**[10:17]** prompt, Claude code is really good at  
**[10:19]** following this. So the idea of like,  
**[10:21]** hey, I want it to remember specific  
**[10:22]** things, this seems like a great place to  
**[10:24]** put it. But we got to be careful because  
**[10:26]** we can overdo it. When we look at  
**[10:28]** studies like this one evaluating  
**[10:29]** agents.md and you can swap agents.md for  
**[10:32]** Claude.md,  
**[10:34]** they found in the study that  
**[10:37]** these sort of files can actually reduce  
**[10:39]** the effectiveness of large language  
**[10:41]** models at large. And why is that? Well,  
**[10:43]** it's because the thing that makes it so  
**[10:44]** good, the fact that it's injected into  
**[10:46]** basically every prompt, is what also can  
**[10:48]** make it so bad. Are we actually  
**[10:51]** injecting the correct  
**[10:53]** context? Have we pushed through the  
**[10:55]** noise and are we actually giving it a  
**[10:56]** proper signal? Or are we just throwing  
**[10:58]** in the in things that we think are good?  
**[11:01]** Because if it isn't relevant to  
**[11:03]** virtually every single prompt it's going  
**[11:04]** to do in your project, should it be here  
**[11:07]** in the Claude.md? Is this a good way to  
**[11:09]** let Claude code remember things?  
**[11:12]** I would argue no, not really. And that  
**[11:15]** goes contrary to what a lot of people  
**[11:17]** say about Claude.md and how you should  
**[11:19]** structure it. Based on studies like that  
**[11:21]** and based on personal experience, less  
**[11:23]** is more. Context pollution is real,  
**[11:25]** context rot is real. So if something is  
**[11:28]** inside of Claude.md and it doesn't make  
**[11:30]** sense for again virtually every single  
**[11:32]** prompt you give it, should it be in  
**[11:34]** there? The answer is no. But most people  
**[11:36]** don't realize that and instead they fall  
**[11:37]** into this trap of a bloated rulebook.  
**[11:40]** Instead, the skills we should be  
**[11:41]** mastering are how do we create project  
**[11:44]** context that is high signal? How do I  
**[11:47]** make sure what I'm actually putting  
**[11:48]** inside this thing makes sense? And with  
**[11:50]** that comes the idea of context rot  
**[11:52]** awareness like we talked about in the  
**[11:53]** last level. And you take all that  
**[11:55]** together and level two feels like you've  
**[11:57]** been moving forward. Like, hey, I'm  
**[11:58]** taking an active role in memory, I have  
**[12:00]** this Claude.md file, you realize  
**[12:02]** it's not really enough.  
**[12:04]** And when we talk about level three and  
**[12:06]** what we can do to move forward there, we  
**[12:08]** want to think about sort of not a static  
**[12:11]** rulebook, but something that can evolve.  
**[12:13]** And it's something that can include  
**[12:15]** Claude.md instead of relying on  
**[12:16]** Claude.md to do everything, what if we  
**[12:18]** use Claude.md as sort of like an index  
**[12:21]** file that points Claude code in the  
**[12:23]** right direction instead. So what did I  
**[12:25]** mean about Claude.md acting as sort of  
**[12:27]** an index and pointing towards other  
**[12:29]** files? Well, I'm talking about a  
**[12:32]** architecture within your codebase that  
**[12:35]** doesn't just have one markdown file  
**[12:37]** trying to deal with all the sort of  
**[12:38]** memory issues in the form of Claude.md.  
**[12:40]** I'm talking about having multiple files  
**[12:42]** for specific tasks. I think a great  
**[12:44]** example of this in action is sort of  
**[12:46]** what GSD, the get done  
**[12:48]** orchestration tool, does. It doesn't  
**[12:50]** just create one file that says, hey,  
**[12:52]** this is what we're going to build are  
**[12:54]** the requirements and this is what we've  
**[12:56]** done and where we're going. Instead, it  
**[12:57]** creates multiple. You can see over here  
**[12:58]** on the left, we have a project.md, a  
**[13:00]** requirements.md, a roadmap and a state.  
**[13:03]** So the requirements  
**[13:05]** exist so Claude code always knows and  
**[13:07]** has memory of what it's supposed to be  
**[13:09]** building. The roadmap breaks down what  
**[13:11]** exactly we are going to be creating not  
**[13:13]** just now, but what we've done in the  
**[13:14]** past and in the future. And the project  
**[13:16]** gives it memory, gives it context of  
**[13:18]** what we are doing at a high-level  
**[13:20]** overview. What is our North Star? And by  
**[13:22]** breaking up memory and context and  
**[13:24]** conventions in this sort of system,  
**[13:26]** we're fighting against the idea of  
**[13:29]** context rot and the idea brought up in  
**[13:31]** that study, which is injecting these  
**[13:33]** files into every prompt all the time  
**[13:35]** like we do in Claude.md. It's actually  
**[13:37]** counterintuitive. It doesn't help us get  
**[13:39]** better outputs. Furthermore, breaking it  
**[13:41]** down into these chunks and having a  
**[13:42]** clear path for Claude code to go down  
**[13:44]** when it says like, hey, I want to figure  
**[13:46]** out where this information is. Oh, I go  
**[13:48]** to Claude.md. Oh, Claude.md says, these  
**[13:50]** are my five options. Okay, here's that  
**[13:52]** one. Let me go and find it. That sort of  
**[13:54]** structure is what you're going to see  
**[13:56]** 100% in the follow-on level when we talk  
**[13:58]** about Obsidian and really is sort of  
**[14:00]** like a crude reimagining of the chunking  
**[14:03]** system and the vector similarity search  
**[14:05]** that we see in true rag systems. But  
**[14:08]** obviously, this is kind of small scale  
**[14:10]** at this level. We're talking about four  
**[14:12]** markdown files here. We're not talking  
**[14:13]** about a system that can handle thousands  
**[14:15]** and thousands and thousands of  
**[14:17]** documents. But like you're going to hear  
**[14:20]** me talk about a lot,  
**[14:21]** what does that mean for you? Do you need  
**[14:24]** a system that we're going to talk about  
**[14:25]** in levels four, five, six, seven that  
**[14:28]** can handle this many documents? The  
**[14:29]** answer is maybe not. And so part of this  
**[14:32]** rag journey is understanding not just  
**[14:34]** where you stand, but like where do you  
**[14:35]** actually need to go? Do you always need  
**[14:37]** to be at level seven and know how to do  
**[14:39]** an agentic rag system inside of Claude  
**[14:41]** code? It's probably good to know how to  
**[14:42]** do it, but it's also just as good to  
**[14:45]** know when you don't need to implement  
**[14:46]** that. Sometimes, what we see in these  
**[14:48]** systems,  
**[14:50]** like this is enough for a lot of people.  
**[14:52]** So  
**[14:52]** it's just as important to know how to do  
**[14:54]** it and to know like, do you need to?  
**[14:57]** Should you do it? When we talk about  
**[14:58]** level three and we talk about state  
**[14:59]** files, how do we know we're here? Well,  
**[15:01]** we know we're here when we're still  
**[15:02]** strictly inside the Claude code  
**[15:03]** ecosystem, we haven't integrated outside  
**[15:05]** tools or applications and really we're  
**[15:07]** just at the place where we're just  
**[15:08]** creating multiple markdown files to  
**[15:10]** create our own homemade sort of like  
**[15:13]** memory chunking system. But this still  
**[15:14]** is really important. We're still  
**[15:15]** mastering some true skills here. The  
**[15:17]** idea of like actually structuring docs,  
**[15:20]** having some sort of system in place that  
**[15:22]** updates state at every session because  
**[15:24]** this is can be a problem with rag, too.  
**[15:25]** Like, how do you make sure everything is  
**[15:27]** up to date? And chances are you're also  
**[15:31]** starting to lean into orchestration  
**[15:32]** layers at this point, things like GSD  
**[15:34]** and superpowers that do things like  
**[15:36]** this, this multi-markdown file  
**[15:38]** architecture on their own. But there is  
**[15:40]** a real trap here. What we create in this  
**[15:42]** project is very much just for that  
**[15:45]** project. It's kind of clunky to then  
**[15:47]** take those markdown files and shift them  
**[15:49]** over to another project. So level four  
**[15:51]** is where we bring in Obsidian. And this  
**[15:53]** is a tool that has been getting a ton of  
**[15:55]** hype and for good reason. When you have  
**[15:57]** people like Andre Karpathy talking about  
**[15:59]** these LLM knowledge bases they've  
**[16:02]** created which are built for all intents  
**[16:04]** and purposes on an Obsidian foundation  
**[16:06]** and it's getting almost 20 million  
**[16:08]** views, we should probably listen and see  
**[16:10]** how this is actually operating. Now, for  
**[16:12]** context, I've done a full deep dive on  
**[16:15]** this Obsidian Andre Karpathy LLM  
**[16:18]** knowledge base, I'll link that above. So  
**[16:20]** if you want to focus on that, how to  
**[16:21]** build that, make sure you check that out  
**[16:23]** above. And what I also want to mention  
**[16:24]** to most people is that this Obsidian  
**[16:26]** thing we're going to talk about right  
**[16:27]** here in level four,  
**[16:29]** this is honestly the level most people  
**[16:31]** should strive for because this is enough  
**[16:34]** for most people in most use cases. When  
**[16:36]** we talk about levels five, six, and  
**[16:37]** seven, we're going to talk about true  
**[16:39]** rag structures and to be honest, it's  
**[16:42]** overkill for most people. This is  
**[16:44]** overkill  
**[16:45]** for most people. Like we love talking  
**[16:48]** about rag, like it's great, I understand  
**[16:49]** that, but Obsidian is that 80% solution  
**[16:53]** that in reality is like a 99% solution  
**[16:55]** for most people because it's free,  
**[16:56]** there's basically no overhead, and it  
**[16:59]** does the job for the solo operator. And  
**[17:01]** when I say it does the job for the solo  
**[17:02]** operator, I mean it solves the problem  
**[17:04]** of having Claude code connected to a  
**[17:07]** bunch of different documents, a bunch of  
**[17:09]** different markdown files, and being able  
**[17:11]** to get accurate, timely information from  
**[17:14]** it and having insight to those documents  
**[17:17]** as the human being. Because when I click  
**[17:19]** on these documents, it's very clear what  
**[17:21]** is going on inside here and it's very  
**[17:22]** clear what documents are related to it.  
**[17:25]** When I click these links,  
**[17:27]** I'm brought to more  
**[17:28]** documents. When I click these links,  
**[17:31]** I'm brought to more documents. And so  
**[17:33]** for me as a human being, having this  
**[17:35]** insight is important. Because to be  
**[17:36]** totally honest, the  
**[17:38]** Obsidian-based  
**[17:40]** insight to the documents, I would argue  
**[17:42]** trumps a lot of the insight you get from  
**[17:44]** the rag systems. When we talk about  
**[17:46]** thousands and thousands of documents  
**[17:48]** being embedded in something like a grab  
**[17:49]** rag system, like this looks great  
**[17:51]** visually, looks very stunning. Do you  
**[17:53]** actually know what's going on inside  
**[17:55]** here?  
**[17:57]** Maybe you do. To be honest, you're kind  
**[17:59]** of just  
**[18:00]** relying on the answers you get that will  
**[18:01]** show in the in the links and stuff, but  
**[18:03]** it's a bit harder. It's like piece  
**[18:04]** through the embeddings for sure. All's  
**[18:06]** that to say is you should pay special  
**[18:08]** attention to Obsidian and Claude code.  
**[18:09]** Because when we talk about this journey  
**[18:11]** from rag, I always suggest to everybody,  
**[18:14]** clients included, like let's just start  
**[18:16]** with Obsidian  
**[18:17]** and see how far we can scale this. And  
**[18:20]** eventually, if we do hit a wall, you can  
**[18:22]** always transition to more robust rag  
**[18:24]** systems.  
**[18:25]** So why not try the simple option? If it  
**[18:27]** works, great, it's free, cost me no  
**[18:29]** money. Versus like, let's try to knock  
**[18:31]** out this rag system which can be kind of  
**[18:33]** difficult to put into production  
**[18:35]** depending on what you're trying to do.  
**[18:36]** Like always start with the simple stuff.  
**[18:38]** It's never too hard to transition to  
**[18:40]** something more complicated. So what are  
**[18:41]** we really talking about here in level  
**[18:43]** four? Well, we're talking about taking  
**[18:45]** sort of that structure we began to build  
**[18:47]** in level three, you know, with an index  
**[18:49]** file pointing to different markdown  
**[18:51]** files, and just scaling that up and then  
**[18:54]** bringing in this outside tool Obsidian  
**[18:56]** to make it easy for you, the human  
**[18:57]** being, to actually see these  
**[18:58]** connections. And the platonic idea of  
**[19:00]** this version is pretty much what Andre  
**[19:01]** Karpathy laid out in building a LLM  
**[19:03]** knowledge base on top of Obsidian and  
**[19:05]** powered by Claude code.  
**[19:06]** And what that looks like is a structure  
**[19:09]** like this. So when you use Obsidian and  
**[19:11]** you download it, it's completely free.  
**[19:12]** Again, reference that video I posted  
**[19:14]** earlier. You set a certain file as the  
**[19:17]** vault. Think of the vault as sort of  
**[19:21]** like the rag system, this this quasi rag  
**[19:23]** system you've created. And inside of the  
**[19:26]** vault, we then  
**[19:28]** architect that, we structure that just  
**[19:30]** with files. So we have the overarching  
**[19:33]** file called the vault and inside that  
**[19:35]** vault, we create multiple subfolders. In  
**[19:37]** Andre Karpathy's case, he talks about  
**[19:39]** three different subfolders. The reality  
**[19:41]** is they could be any subfolders. It just  
**[19:43]** sort of needs to match the theme we're  
**[19:45]** going to talk about.  
**[19:47]** In one folder, we have the raw data.  
**[19:48]** This is everything we are ingesting and  
**[19:50]** eventually want to structure so that  
**[19:52]** Claude code can reference it later.  
**[19:54]** Think of, you know, you have Claude code  
**[19:56]** do competitive analysis on 50 of your  
**[19:59]** competitors and it pulls 50 sites for  
**[20:01]** each, right? We're talking about a large  
**[20:03]** amount of information. It's about 2,500  
**[20:05]** different things. All that will get  
**[20:06]** dumped into some sort of raw folder.  
**[20:08]** This is like the staging area for the  
**[20:10]** data. We then have the wiki folder. The  
**[20:12]** wiki folder is where the structured data  
**[20:14]** goes. So, we then have Claude code take  
**[20:17]** this raw data and structure it into  
**[20:19]** essentially different like Wikipedia  
**[20:21]** type articles inside of the wiki folder.  
**[20:24]** Each article gets its own folder. So,  
**[20:28]** the idea being when you then ask Claude  
**[20:30]** code information about, you know, let's  
**[20:32]** say we had it search for stuff about AI  
**[20:34]** agents. And I say, "Hey, Claude code,  
**[20:36]** talk to me about AI agents." The same  
**[20:38]** way you would query a rag system.  
**[20:41]** Well, Claude code is going to go to the  
**[20:43]** vault.  
**[20:44]** From the vault, it's going to go to the  
**[20:45]** wiki. The wiki has a master index  
**[20:48]** markdown file. Think of sort of what we  
**[20:50]** were doing with talked about doing with  
**[20:51]** Claude.md before, right? You see how  
**[20:53]** these  
**[20:54]** sort of themes transition throughout the  
**[20:56]** different levels.  
**[20:58]** It takes a look at that master index.  
**[20:59]** The master index tells it what exists in  
**[21:02]** the subsidiary rag system. Oh, AI agents  
**[21:04]** exist. Cool. Guess what's going on down  
**[21:06]** here. It also has an index file which  
**[21:09]** talks about the individual articles that  
**[21:11]** exists.  
**[21:12]** What am I saying here? I am saying there  
**[21:15]** is a clear hierarchy for Claude code to  
**[21:19]** reference when it wants to find  
**[21:20]** information about files. Vault, wiki,  
**[21:24]** index, article,  
**[21:26]** etc. So, because it is so clear how to  
**[21:30]** find information, also why it's so clear  
**[21:32]** to first find information and turn it  
**[21:34]** into wiki, we can create a system that  
**[21:36]** has a lot of documents without rag.  
**[21:40]** Hundreds, thousands if you do this  
**[21:42]** properly. Because if the system is  
**[21:44]** clear, hey, I check the vault and I  
**[21:45]** check the index and that has a clear  
**[21:48]** delineation of like where everything is,  
**[21:50]** well, then it's not too hard for Claude  
**[21:51]** code to figure out where to find stuff.  
**[21:53]** And so, you can get away with a non-rag  
**[21:55]** structure for thousands of documents and  
**[21:56]** it's been really hard to do that in the  
**[21:58]** past. And that's because most people  
**[21:59]** don't structure anything with any sort  
**[22:01]** of structure. They just have a billion  
**[22:02]** documents sitting in one folder. It's  
**[22:04]** the equivalent of having 10 million  
**[22:05]** files strewn across the factory floor. I  
**[22:08]** mean like, "Well, Claude code, find it."  
**[22:11]** Like no, you actually just need a filing  
**[22:12]** cabinet. Like Claude code's actually  
**[22:14]** pretty smart. And you can see that  
**[22:15]** architecture in action right here. So,  
**[22:17]** right now we're looking at a Claude.md  
**[22:18]** file that is in an Obsidian vault. And  
**[22:22]** what does it say? Well, breaks down the  
**[22:24]** vault structure, the wiki system, you  
**[22:26]** know, the overall structure of the  
**[22:28]** subfolders, and how to essentially work  
**[22:31]** it, right? So, again, we're using  
**[22:33]** Claude.md as a conventions type file.  
**[22:35]** Over here on the left, you can see the  
**[22:37]** wiki folder. Inside the wiki folder is a  
**[22:39]** master index and it lists what is inside  
**[22:43]** of there. In this case, there's just one  
**[22:45]** article and it's on Claude managed  
**[22:47]** agents. Inside that folder, we see  
**[22:50]** Claude managed agents. It has its own  
**[22:52]** wiki folder breaking down the articles  
**[22:53]** inside until you get to the actual  
**[22:56]** article itself. So, very clear the steps  
**[22:58]** it needs to take. And so, when I tell  
**[23:00]** Claude code, "Talk to me about the  
**[23:02]** managed agents. We have a wiki on it."  
**[23:04]** It's very easy for it to search for it  
**[23:06]** via its built-in grep tool. It links me  
**[23:09]** the actual markdown file and then breaks  
**[23:11]** down everything that's happening. Now,  
**[23:13]** the question at level four really  
**[23:14]** becomes a level of scale. How many  
**[23:16]** documents can we get away with where  
**[23:18]** this sort of system continues to work?  
**[23:20]** Is there a point at which Andrej  
**[23:22]** Karpathy's system begins to fall apart  
**[23:24]** where, hey, like I get it. It's a very  
**[23:25]** clear clear path that Claude code needs  
**[23:27]** to follow. It goes to the indexes, yada  
**[23:28]** yada yada.  
**[23:30]** Does that sustain itself at  
**[23:32]** 2,000 documents? 2,500? 3,000? Is there  
**[23:35]** a clear number? The answer is we don't  
**[23:37]** really know and there isn't a clear  
**[23:38]** number because  
**[23:39]** all your documents are also different.  
**[23:41]** And in terms of hitting a wall, it isn't  
**[23:43]** just as simple as, well, Claude code's  
**[23:45]** giving us the wrong answers. It has too  
**[23:47]** many files in Obsidian system. How much  
**[23:49]** is it costing you in terms of tokens now  
**[23:50]** that we've added so many files and how  
**[23:52]** quickly is it doing it? Because rag can  
**[23:55]** actually be infinitely faster and  
**[23:57]** cheaper in certain situations. What  
**[23:59]** we're looking at here is a comparison  
**[24:02]** between textual LLMs, right, in the  
**[24:05]** giant bars, and textual rag in terms of  
**[24:07]** the amount of tokens it took to get to  
**[24:09]** the correct answer, and the amount of  
**[24:10]** time it took to get that answer. What do  
**[24:13]** we see here? We see that textual rag  
**[24:16]** versus textual LLMs, there's a massive  
**[24:18]** difference to the tune of like 1,200  
**[24:20]** times.  
**[24:21]** I'm saying rag is 1,200 times cheaper  
**[24:24]** and 1,200 times faster than textual LLM  
**[24:27]** in these studies. Now, context. This was  
**[24:30]** done in 2025. This was not done with  
**[24:33]** Claude code. These models have changed  
**[24:35]** significantly since then. These are just  
**[24:36]** straight-up LLMs. This isn't a coding  
**[24:38]** artist.  
**[24:39]** Etcetera, etc., etc. However, we were  
**[24:42]** talking a 1,200x  
**[24:45]** difference. So, when we're evaluating,  
**[24:48]** hey, is Obsidian what I should be doing  
**[24:51]** versus is should I be doing rag system,  
**[24:53]** it isn't as simple as just, well, it's  
**[24:56]** giving me the right answer or not.  
**[24:57]** Because you could be you could have a  
**[24:58]** scenario where you get the right answer  
**[24:59]** with Obsidian, yet if you went to rag,  
**[25:02]** it's  
**[25:03]** a thousand times cheaper and faster.  
**[25:06]** Right? So, it's this very fuzzy line  
**[25:08]** between when is Obsidian good enough and  
**[25:10]** these sort of like just markdown file  
**[25:12]** architectures good enough or when like  
**[25:14]** we need to use rag. There's not a great  
**[25:15]** answer. I don't have a great answer for  
**[25:17]** you. The answer is you have to  
**[25:17]** experiment and you need to try both and  
**[25:19]** see what works. Because this is frankly  
**[25:22]** out of date.  
**[25:23]** Totally. Like 2025, older models. The  
**[25:26]** difference between rag and textual LLMs  
**[25:28]** is not 1,200 times.  
**[25:30]** But how much has that gap shrunk?  
**[25:32]** Because that is an insane gap. That  
**[25:33]** isn't like 10x. It's 1,200x.  
**[25:37]** The So, there's a lot you have to know.  
**[25:39]** And again, you you won't know the answer  
**[25:42]** ahead of time. You just won't. Watch  
**[25:44]** every video you want. No one's going to  
**[25:45]** tell you where that line in the sand is.  
**[25:47]** You literally just need to experiment  
**[25:49]** and see what works for you as you  
**[25:51]** increase the amount of documents you're  
**[25:53]** asking Claude code to answer questions  
**[25:54]** about. So, on that note, let's move on  
**[25:56]** to level five, which is where we finally  
**[25:59]** begin to talk about real rag systems and  
**[26:02]** talk about some of the rag fundamentals  
**[26:03]** like embeddings, vector databases, and  
**[26:05]** how data actually flows through a system  
**[26:08]** when it becomes part of our rag  
**[26:10]** knowledge base. So, let's begin by  
**[26:12]** talking about naive rag, which is the  
**[26:13]** most basic type of rag out there. But it  
**[26:16]** provides the foundation for everything  
**[26:18]** else we do. Now, you can kind of think  
**[26:20]** of rag systems being broken out into  
**[26:22]** three parts. On the left-hand side, we  
**[26:24]** have the embedding stage. We then have  
**[26:27]** the vector database. And then we have  
**[26:30]** the actual retrieval going on with the  
**[26:32]** large language model. So, one, two, and  
**[26:35]** three. And to best illustrate this  
**[26:37]** model, let's start with sort of the  
**[26:40]** journey of a document that is going to  
**[26:42]** be part of our knowledge base. Remember,  
**[26:43]** any large rag system, we could be  
**[26:45]** talking about thousands of documents and  
**[26:47]** and each document could be thousands of  
**[26:49]** pages. But in this example, we have a  
**[26:51]** one-page document that we're talking  
**[26:53]** about. Now, if we want to add this  
**[26:56]** document to our database, the way it's  
**[26:58]** going to work is it's not going to be  
**[27:00]** ingested as a whole unit. Instead, we  
**[27:03]** are going to take this document and we  
**[27:04]** are going to chunk it up into pieces.  
**[27:07]** So, this one-pager essentially becomes  
**[27:10]** three different chunks. These three  
**[27:12]** chunks are then sent to an embedding  
**[27:14]** model. And the job of the embedding  
**[27:16]** model is to take these three chunks and  
**[27:19]** turn it into a vector in a vector  
**[27:21]** database. Now, a vector database is  
**[27:25]** just a different variation of your  
**[27:26]** standard database. When we talk about a  
**[27:28]** standard database,  
**[27:29]** think of something like an Excel  
**[27:31]** document, right? You have columns and  
**[27:32]** you have rows.  
**[27:34]** Well, in a vector database, it's not  
**[27:36]** two-dimensional columns and rows. It's  
**[27:37]** actually hundreds if not thousands of  
**[27:40]** dimensions. But for the purposes of  
**[27:42]** today, just think of a three-dimensional  
**[27:44]** graph like you see here.  
**[27:46]** And the vectors are just points in that  
**[27:49]** graph. And each point is represented by  
**[27:51]** a series of numbers. So, you can see  
**[27:54]** here, we have bananas and bananas is  
**[27:57]** represented by 0.52,  
**[27:59]** 5.12, and then 9.31. You see that up  
**[28:02]** here. Now, that continues for hundreds  
**[28:05]** of numbers. Now, where each vector gets  
**[28:07]** placed in this giant multi-dimensional  
**[28:10]** graph depends on its semantic meaning.  
**[28:14]** What What do the words actually mean?  
**[28:16]** So, you can see over here. This is like  
**[28:17]** the the fruit section. We have bananas.  
**[28:20]** We have apples. We have pears. Over  
**[28:22]** here, we have ships and we have boats.  
**[28:24]** So, going back to our document, let's  
**[28:26]** imagine that this document is about  
**[28:29]** World War II ships. So, each of these  
**[28:32]** chunks is going to get turned into a  
**[28:35]** series of numbers and those series of  
**[28:37]** numbers will be represented as a dot in  
**[28:39]** this graph. Where do you think it's  
**[28:40]** going to go? Well, they'll probably go  
**[28:42]** around this area, right? So, that'd be  
**[28:44]** one, two, and three. So, that's how  
**[28:47]** documents get placed. Every document is  
**[28:49]** going to get chunked. Each chunk goes  
**[28:51]** through the embedding model and the  
**[28:53]** embedding model inserts them into the  
**[28:55]** vector database. Repeat, repeat, repeat  
**[28:57]** for every single document. And in the  
**[28:58]** end, after we do that several thousand  
**[28:59]** times, we get a vector database which  
**[29:02]** represents our knowledge graph, so to  
**[29:04]** speak, our our our knowledge base. And  
**[29:06]** that moves us on to step three, which is  
**[29:08]** the retrieval part. So, where do you  
**[29:10]** play into this? Well,  
**[29:12]** normally,  
**[29:13]** let's let's depict you. Well, we'll  
**[29:15]** we'll give you a different color. You  
**[29:16]** can be  
**[29:17]** you're going to be pink.  
**[29:19]** So, this is you. All right?  
**[29:21]** You normally just talk to Claude code  
**[29:24]** and you ask Claude code questions about  
**[29:26]** World War battleships. Well, in your  
**[29:29]** standard non-rag setup, what's going to  
**[29:31]** happen? Well, the large language model  
**[29:33]** Opus 4.6 is going to take a look at its  
**[29:35]** training data and then it's going to  
**[29:37]** give you an answer based on its training  
**[29:38]** data information about World War  
**[29:40]** battleships. But with a rag system, it's  
**[29:42]** going to do more. It's going to retrieve  
**[29:45]** the appropriate vectors. It's going use  
**[29:48]** those vectors to augment the answer it  
**[29:50]** generates for you. Hence,  
**[29:52]** retrieval-augmented generation. That's  
**[29:54]** the power of rag. It allows our large  
**[29:56]** language models to pull in information  
**[29:59]** that is not a part of its training data  
**[30:01]** to augment its answer. In this example,  
**[30:03]** World War II battleships, yes, I  
**[30:04]** understand the large language model  
**[30:06]** already knows that, but  
**[30:07]** replace this with  
**[30:09]** any sort of proprietary company data  
**[30:12]** that isn't just available for the web.  
**[30:15]** And do it at scale. That's the sell for  
**[30:17]** rag. Now, in our example, when we ask  
**[30:19]** Claude Code for questions for  
**[30:21]** information about World War II  
**[30:22]** battleships and it's in a rag setup,  
**[30:24]** what it's going to do is it's going to  
**[30:25]** take our question  
**[30:27]** and it's going to turn our question into  
**[30:30]** a series of numbers similar to the  
**[30:32]** vectors over here. It is then going to  
**[30:34]** take a look at what the number is for  
**[30:37]** our question and the numbers of the  
**[30:39]** vectors and it's going to see which of  
**[30:41]** these vectors most closely matches  
**[30:44]** question's  
**[30:45]** vector, right? How similar are the  
**[30:47]** vectors to the question, pretty much.  
**[30:49]** And then it's going to pull a certain  
**[30:51]** amount of vectors, whether that's 1 2 3  
**[30:53]** 4 5 or 10 or 20, and it's going to pull  
**[30:56]** those vectors and their information  
**[30:59]** into the large language model. So, now  
**[31:01]** the large language model has its  
**[31:03]** training data answer plus say 10 vectors  
**[31:05]** worth of information.  
**[31:07]** Right? That was the retrieval part. And  
**[31:09]** then it augments and generates an answer  
**[31:10]** with that additional information, and  
**[31:12]** that is how rag works. That is how naive  
**[31:15]** rag works. Now, this is not particularly  
**[31:17]** effective for a number of reasons. This  
**[31:19]** very basic structure kind of falls apart  
**[31:22]** at the beginning when we begin to think  
**[31:23]** about, "Okay,  
**[31:25]** how are we chunking up these documents?  
**[31:28]** Is it random? Is it off just off a pure  
**[31:30]** number of tokens? Do we have a certain  
**[31:32]** number of overlap? Are the documents  
**[31:34]** themselves set up in a way where it even  
**[31:36]** makes sense to chunk them?  
**[31:38]** Because what if, you know, chunk number  
**[31:40]** three is referencing something in chunk  
**[31:42]** number one, and then our vector  
**[31:44]** situation when we pull the chunks, what  
**[31:46]** if it doesn't get the right one? What if  
**[31:47]** it doesn't get that other chunk that's  
**[31:50]** required as context to even make sense  
**[31:52]** of what number three says? You get what  
**[31:53]** I'm saying?  
**[31:54]** Like very often, the entire document  
**[31:57]** itself is needed to answer questions  
**[31:59]** about said document. So, this idea of  
**[32:02]** getting these piecemeal answers  
**[32:04]** doesn't really work in practice. Yet,  
**[32:06]** this is how rag was set up for a long,  
**[32:08]** long time. Other issues that can come  
**[32:10]** into play are things like, "What if I  
**[32:12]** have questions about the relationships  
**[32:15]** between different vectors?" Because  
**[32:17]** right now, I kind of just pull vectors  
**[32:19]** in a silo, but what if I wanted to know  
**[32:21]** how boats related to bananas?  
**[32:24]** Sounds random, but what if I did? You  
**[32:26]** know, this standard sort of vector  
**[32:30]** database naive rag approach,  
**[32:31]** everything's kind of in a silo. It's  
**[32:33]** hard to connect information, and a lot  
**[32:35]** of it just depends on  
**[32:37]** how well those original documents are  
**[32:40]** even structured. Are they structured in  
**[32:41]** a manner that makes sense for rag? Now,  
**[32:43]** over the years, we've come up with some  
**[32:44]** ways to alleviate these issues, things  
**[32:46]** like re-rankers or ranking systems that  
**[32:49]** take a look at all of the vectors we  
**[32:50]** grab and essentially then do another  
**[32:52]** pass on them with a large language model  
**[32:54]** to rank them in terms of their  
**[32:55]** relevance. But by and large, this naive  
**[32:58]** rag system  
**[33:00]** has kind of fallen out of vogue. Yet,  
**[33:02]** still important to understand how this  
**[33:03]** works at a foundational level, so it can  
**[33:05]** inform your decisions if you go for a  
**[33:07]** more robust rag approach. Because if you  
**[33:10]** don't understand how chunking or  
**[33:11]** embeddings even work, how can you make  
**[33:14]** decisions about how you should structure  
**[33:15]** your documents when we talk about  
**[33:17]** something like graph rag or we talk  
**[33:19]** about more complicating embedding  
**[33:21]** systems like the brand new one from  
**[33:22]** Google which can actually ingest not  
**[33:24]** just text, but videos. And if you don't  
**[33:26]** understand the sort of foundation, it's  
**[33:28]** hard for you to actually understand this  
**[33:29]** trap. And the trap is that we've kind of  
**[33:32]** just created a crappy search engine.  
**[33:34]** Because with these naive rag systems  
**[33:36]** where all we do is grab chunks and we  
**[33:37]** can't really understand the  
**[33:39]** relationships between them, how is that  
**[33:41]** different from basically just having an  
**[33:44]** overcomplicated control F system? The  
**[33:47]** answer to this is really not much of a  
**[33:48]** difference, which is why in these simple  
**[33:51]** in these simplistic kind of outdated rag  
**[33:54]** structures that actually are still all  
**[33:55]** over the place. If you see someone who's  
**[33:56]** like, "Oh, here's my pinecone rag system  
**[33:59]** or here's my superbase rag system." They  
**[34:01]** don't mention anything about graph rag  
**[34:03]** or they don't mention anything about  
**[34:05]** like, "Hey, here's how we have like the  
**[34:06]** sophisticated re-ranker system." And  
**[34:07]** they  
**[34:08]** it's going to suck to the tune of like,  
**[34:10]** "Oh, the actual effectiveness of this is  
**[34:12]** like 25% of the time you get something  
**[34:14]** right."  
**[34:15]** Like you're almost better guessing.  
**[34:17]** So, if you don't know that going in, you  
**[34:18]** can definitely be  
**[34:20]** sort of hoodwinked or confused or in  
**[34:22]** some cases like basically scammed into  
**[34:24]** buying these rag systems that do not  
**[34:25]** make sense. And so, level five isn't  
**[34:27]** about implementing these sort of naive  
**[34:29]** rag systems. It's about understanding  
**[34:31]** how they work so that you when it comes  
**[34:34]** time to implement something more  
**[34:35]** sophisticated, you actually understand  
**[34:38]** what's going on. Because that  
**[34:39]** five-minute explanation of rag is sadly  
**[34:41]** not something most people understand  
**[34:42]** when they say, "I need a rag system."  
**[34:44]** Well, do you? Because you also have to  
**[34:46]** ask yourself, what kind of questions are  
**[34:48]** you actually asking about your system?  
**[34:50]** If you're just asking, you know,  
**[34:53]** essentially treating your knowledge base  
**[34:54]** as a giant rulebook and you just need  
**[34:56]** specific things from that knowledge  
**[34:58]** system brought up, well then Obsidian's  
**[35:00]** probably enough or you could probably  
**[35:02]** even get away with a naive rag system.  
**[35:03]** But if we need to know about  
**[35:04]** relationships, if we need to know about  
**[35:06]** how X interacts with Y and they're two  
**[35:09]** separate documents, they never even  
**[35:11]** really mention each other,  
**[35:13]** and it's not something I can just stick  
**[35:14]** inside the context directly because I  
**[35:16]** have thousands of said documents. Well,  
**[35:18]** that is where when you're going to need  
**[35:20]** rag, and that's when you're going to  
**[35:21]** need something more sophisticated than  
**[35:23]** basic vector rag. That  
**[35:26]** is when we need to start talking about  
**[35:27]** graph rag. So, when we talk about level  
**[35:29]** six of Claude Code and rag, we're  
**[35:31]** talking about this. And in my opinion,  
**[35:34]** if you are going to use rag, this is  
**[35:36]** sort of the lowest level of  
**[35:38]** infrastructure you need to create. This  
**[35:40]** is using Light Rag, which is a  
**[35:41]** completely open-source tool. I'll put a  
**[35:43]** link above where I break down exactly  
**[35:45]** how to use it and how to build it. But  
**[35:47]** the idea of graph rag is pretty obvious.  
**[35:50]** It's the idea that everything is  
**[35:51]** connected. This isn't a vector database  
**[35:53]** with a bunch of vectors in a silo. This  
**[35:56]** is a bunch of things connected to one  
**[35:57]** another, right? I click on this  
**[35:58]** document, I can see over here on the  
**[36:00]** right, and I'll move this over, you  
**[36:01]** know, the description of the vector, the  
**[36:04]** name, the type, the file, the chunk, and  
**[36:06]** then more importantly, the different  
**[36:08]** relationships. And this  
**[36:09]** relationship-based approach results in  
**[36:12]** more effective outcomes. Here is a chart  
**[36:14]** from Light Rag's GitHub. I would say 6  
**[36:17]** to 8 months old. And  
**[36:19]** also of note, Light Rag is the lightest  
**[36:22]** weight graph rag system out there that I  
**[36:24]** know of. There are some very robust  
**[36:26]** versions including graph rag itself from  
**[36:30]** Microsoft. It's a graph It's literally  
**[36:31]** called graph rag. But when we compare  
**[36:33]** naive rag to Light Rag across the board,  
**[36:36]** we get jumps of often times more than  
**[36:39]** 100%, right? 31.6 versus 68.4, 24 versus  
**[36:44]** 76, 24 versus 75, on and on and on. And  
**[36:48]** that being said, according to Light Rag,  
**[36:49]** it actually holds its own and beats out  
**[36:51]** graph rag itself, but hey, these are  
**[36:53]** Light Rag's numbers, so take it with a  
**[36:55]** grain of salt. Now, when we look at this  
**[36:56]** knowledge graph system, right away your  
**[36:58]** mind probably goes to Obsidian. Because  
**[37:00]** this looks very similar. However, what  
**[37:03]** we're looking at here in Obsidian is  
**[37:05]** way more rudimentary than what's going  
**[37:07]** on inside of Light Rag or any graph rag  
**[37:09]** system. Because this series of  
**[37:11]** connections we see here,  
**[37:13]** this is all manual and somewhat  
**[37:15]** arbitrary. It's only connected because  
**[37:17]** we set related documents or Claude Code  
**[37:20]** set related documents when it generated  
**[37:22]** this particular document, for example.  
**[37:23]** Just added a couple brackets, boom, that  
**[37:26]** document's connected. So, in theory, I  
**[37:27]** could connect a bunch of random  
**[37:29]** documents that in reality have nothing  
**[37:30]** to do with one another. Now, because  
**[37:31]** Claude Code isn't stupid, it's not going  
**[37:33]** to do that, but that's a lot different  
**[37:35]** than what went on here. Like this went  
**[37:36]** through an actual embedding system. It  
**[37:40]** looked at the actual content, it set a  
**[37:42]** relationship, it set an entity. There's  
**[37:44]** a lot more work going on here inside of  
**[37:46]** Light Rag in terms of defining the  
**[37:48]** relationships than Obsidian. Now, does  
**[37:51]** that difference actually equate to some  
**[37:53]** wild gap in terms of the performance?  
**[37:57]** At a low level, no. At a huge scale,  
**[38:01]** maybe.  
**[38:02]** Again, we're in sort of that gray area.  
**[38:04]** Kind of depends on your scale and what  
**[38:06]** we're actually talking about, and nobody  
**[38:08]** can answer that question except you and  
**[38:10]** some personal experience. But  
**[38:11]** understand, these two things  
**[38:14]** are not the same. We are not the same,  
**[38:16]** brother.  
**[38:17]** Two totally different systems. One is  
**[38:20]** pretty sophisticated, one's pretty  
**[38:22]** rudimentary. Understand that. And so, to  
**[38:24]** wrap up level six in graph rag, we're  
**[38:26]** really here when we're when we've  
**[38:28]** decided, "Hey, stuff like Obsidian isn't  
**[38:30]** working. We can't use something like  
**[38:32]** naive rag cuz it just doesn't work, and  
**[38:33]** we need something that can extract  
**[38:35]** entities and relationships and really  
**[38:38]** leverage the sort of hybrid vector plus  
**[38:41]** graph query system design." But there  
**[38:44]** are some traps. There are some serious  
**[38:46]** roadblocks even here at level six. When  
**[38:48]** we talk about Light Rag, this is just  
**[38:49]** text.  
**[38:51]** What if I have scannable PDFs? What if I  
**[38:53]** have videos? What if I have images? We  
**[38:56]** don't live in a world where all your  
**[38:57]** documents are just going to be Google  
**[38:58]** Docs.  
**[39:00]** And so, what do we do in those  
**[39:02]** instances? So, multimodal retrieval is a  
**[39:04]** huge thing, and on top of that, what  
**[39:06]** about bringing some more agentic  
**[39:07]** qualities to these systems? Give it a  
**[39:09]** little more AI power, some sort of boost  
**[39:11]** in that department. Well, if we're  
**[39:13]** talking about things that are  
**[39:14]** multimodal, then we can finally move to  
**[39:17]** sort of like the bleeding edge of rag in  
**[39:20]** today's day and age as of April 2026.  
**[39:24]** And that's what level seven's all about.  
**[39:25]** Now, when we talk about level seven  
**[39:26]** agentic rag, the big thing we kind of  
**[39:30]** want to index on here is things that  
**[39:32]** have to do with multimodal ingestion.  
**[39:34]** Now, we've done videos on these things,  
**[39:36]** things like rag anything, which allow us  
**[39:39]** to import images and non-text documents.  
**[39:42]** Again, think scannable PDFs into  
**[39:44]** structures like the light rag knowledge  
**[39:46]** graph you saw here. We also have new  
**[39:48]** releases like Gemini embedding, too,  
**[39:50]** which just came out in March, which  
**[39:52]** allows us to actually embed videos into  
**[39:55]** our vector database, videos itself. And  
**[39:57]** this is frankly where the space is  
**[39:59]** going. It's not enough to just do text  
**[40:01]** documents. How much information, how  
**[40:03]** much knowledge is trapped on the  
**[40:05]** internet, especially on places like  
**[40:06]** YouTube, which is purely video?  
**[40:08]** And we want more than just a transcript,  
**[40:10]** as well. A transcript doesn't do enough.  
**[40:12]** So, this sort of multimodal problem is  
**[40:14]** real, and again, this is stuff that just  
**[40:16]** came out weeks ago. And level seven is  
**[40:18]** also where we need to start paying  
**[40:19]** attention to our architecture and  
**[40:21]** pipelines when it comes to the data  
**[40:23]** going in and out of our rag system. It's  
**[40:25]** not enough to just get data in here.  
**[40:26]** Like, this is great. You know, okay, we  
**[40:29]** have all these connections and stuff.  
**[40:30]** Oh, how is the data getting there? How  
**[40:32]** is the data getting there in the context  
**[40:34]** of a team? How is data getting out of  
**[40:36]** there? Like, what if some of the  
**[40:38]** information here has changed in a  
**[40:40]** particular document? What if somebody  
**[40:41]** edits it? How does it get updated? What  
**[40:43]** if we add duplicates?  
**[40:45]** Who can actually put these things in  
**[40:47]** there? When it comes to production-level  
**[40:49]** stuff, these are all questions you need  
**[40:50]** to begin to ask yourself. And so, when  
**[40:52]** we look at an agentic rag system like  
**[40:54]** this one from N8N, you can see the vast  
**[40:56]** majority of the infrastructure,  
**[40:59]** everything outlined here, is all about  
**[41:01]** data ingestion and data syncing. There's  
**[41:04]** only a very small part that has anything  
**[41:05]** to do with rag, which is right there.  
**[41:07]** Because we need systems that clean up  
**[41:09]** the data, that are able to look at,  
**[41:10]** "Okay, we just ingested this document.  
**[41:13]** In fact, this is version two of version  
**[41:15]** one. Can we now go back and clean that  
**[41:17]** data?" Here's something like a data  
**[41:18]** ingestion pipeline, where documents  
**[41:20]** don't get directly put into the system.  
**[41:22]** In light rag, we instead put it inside  
**[41:24]** of like a Google Drive. And from there,  
**[41:26]** it gets ingested into the graph rag  
**[41:28]** system and logged. These are the sort of  
**[41:29]** things that will actually make or break  
**[41:31]** your rag system when you're using it for  
**[41:33]** real. And when we talk about agentic  
**[41:35]** rag, you can see here, and I know this  
**[41:38]** is rather blurry, but if we have an AI  
**[41:40]** agent running this whole program. So,  
**[41:41]** you set up imagine some sort of chatbot  
**[41:43]** for your team. Does it always need to  
**[41:45]** hit  
**[41:46]** this database?  
**[41:48]** The answer is probably not. Chances are,  
**[41:51]** in a team setting, in a business  
**[41:53]** setting, you're going to have  
**[41:54]** information that's in a database like  
**[41:55]** this, like text or something, but you  
**[41:56]** probably also have another set of  
**[41:59]** databases, like just standard Postgres  
**[42:00]** databases with a bunch of information  
**[42:02]** you want to query with SQL, as well. So,  
**[42:05]** when we talk about an agentic rag  
**[42:07]** system, we need something that has all  
**[42:08]** of that, the ability to intelligently  
**[42:10]** decide, "Oh, am I going to be hitting  
**[42:13]** the graph rag database represented here,  
**[42:15]** or am I just going to be doing some sort  
**[42:17]** of SQL queries in Postgres?" These  
**[42:19]** things can get complicated, right? And  
**[42:21]** all of this is use case dependent, which  
**[42:22]** is why it's kind of hard to sometimes  
**[42:24]** make these videos and try to hit every  
**[42:26]** single edge case. The point here at  
**[42:28]** level seven is not that there's  
**[42:30]** necessarily some super rag system you've  
**[42:32]** never heard of. It's that you're  
**[42:34]** actually the devil's in the details  
**[42:36]** here, and that's really mostly the data  
**[42:38]** ingestion piece and keeping it up to  
**[42:40]** date, but also like, how do you actually  
**[42:42]** access this thing? Easy to do in a demo  
**[42:45]** right here. Oh, we just go to the light  
**[42:46]** rag thing and I go to retrieval and ask  
**[42:48]** a questions. Different scenario when  
**[42:50]** we're talking about it with a team, and  
**[42:53]** everyone's approaching it from different  
**[42:54]** angles, and you probably don't want  
**[42:55]** everyone to have access to actually  
**[42:57]** uploading it  
**[42:59]** to light rag itself on a web app. That  
**[43:01]** being said, for the solo operator who is  
**[43:04]** trying to create some sort of  
**[43:06]** sophisticated rag system that is able to  
**[43:09]** do multimodal stuff, I would suggest the  
**[43:12]** rag anything plus light rag combination.  
**[43:14]** I've done a video on that, and I'll If I  
**[43:16]** don't link that already, I'll link it  
**[43:17]** above. I suggest that for a few reasons.  
**[43:19]** One, it's open source, and it's  
**[43:22]** lightweight. So, it's not like you're  
**[43:25]** spending a bunch of money or time to  
**[43:27]** spin something like this up to make sure  
**[43:29]** it actually makes sense for your use  
**[43:30]** case. Again, the thing we want is we  
**[43:33]** don't want to get stuck in systems where  
**[43:36]** there's no way out, and we spent a bunch  
**[43:37]** of money to get there, which is why I do  
**[43:39]** love Obsidian, and I always recommend  
**[43:41]** things like light rag and rag anything.  
**[43:43]** Cuz hey, if you try this out and it  
**[43:44]** doesn't work for you, and it doesn't  
**[43:45]** make sense, okay, whatever. You wasted a  
**[43:47]** handful of hours. You know, it's not  
**[43:48]** like you  
**[43:50]** are spending a bunch of money on  
**[43:51]** Microsoft's graph rag, which is in no  
**[43:54]** in no way is cheap. And so, when do you  
**[43:56]** know you're in level seven? Really  
**[43:58]** multimodal stuff. Like, you need to  
**[43:59]** index images, tables, and videos, and  
**[44:02]** you're integrating some sort of agent  
**[44:03]** system where it can intelligently decide  
**[44:05]** like which path it goes down to answer  
**[44:07]** information. Because at level seven,  
**[44:09]** you're probably integrating all of this  
**[44:11]** stuff. You probably have a Claude MD  
**[44:12]** file with some permanent information.  
**[44:14]** You probably have it in a code base with  
**[44:15]** some markdown files that sort of make  
**[44:17]** sense for easy retrieval. Perhaps you're  
**[44:19]** also including Obsidian. It's in some  
**[44:20]** sort of vault. Plus, you probably have  
**[44:22]** some section of documents that are in a  
**[44:24]** graph rag database, and you have a  
**[44:28]** top of the funnel AI system that can  
**[44:31]** decide, "They asked this question, I go  
**[44:32]** down this route."  
**[44:34]** That's a mature sort of memory  
**[44:36]** architecture  
**[44:38]** that I would suggest. But what's the  
**[44:40]** trap here? The trap, honestly, is trying  
**[44:42]** to force yourself into this level and  
**[44:45]** this sort of sophistication when it's  
**[44:47]** just not needed. To be honest, after all  
**[44:49]** this,  
**[44:50]** most of you're fine with Obsidian. This  
**[44:52]** is more than enough. You don't need  
**[44:53]** graph rag. You really don't need rag in  
**[44:55]** general. And if it's not obvious that  
**[44:57]** you need level seven, and certainly if  
**[44:59]** you haven't already tried the Obsidian  
**[45:00]** route, you don't need to be here. It's  
**[45:01]** probably a waste of your time. But, the  
**[45:03]** whole point of this video was, to the  
**[45:06]** best of my ability, was to expose you to  
**[45:08]** what I see as the different levels of  
**[45:10]** rag and memory and Claude code, and what  
**[45:12]** this problem is, what some of the  
**[45:14]** tensions are, what the tradeoffs are,  
**[45:16]** and where you should probably be for  
**[45:18]** your use case. And again, the biggest  
**[45:21]** thing is just experiment. You don't have  
**[45:23]** to know the answer before you get into  
**[45:24]** this. Just try them out. And I would try  
**[45:26]** it in ascending order. If you can get  
**[45:28]** away with just markdown files and a  
**[45:30]** Claude system, and it's basically just  
**[45:31]** Claude.md on steroids, sweet. Go ahead.  
**[45:34]** And then try Obsidian. If Obsidian's not  
**[45:35]** enough, try light rag, and so on and so  
**[45:38]** forth. So, that is where I'm going to  
**[45:39]** leave you guys for today. If you want to  
**[45:41]** learn more, especially about the  
**[45:42]** production side of rag, like how to spin  
**[45:44]** this up for a team, or package it for a  
**[45:46]** client, we have a whole module on that  
**[45:48]** inside of Chase AI Plus, so check that  
**[45:49]** out. Other than that, let me know what  
**[45:52]** you thought. I know this was a long one,  
**[45:54]** and I will see you around.  