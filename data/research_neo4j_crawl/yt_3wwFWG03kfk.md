# Transcript: https://www.youtube.com/watch?v=3wwFWG03kfk

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 595

---

**[00:09]** Uh, thank you for that. So, over the  
**[00:12]** next 30 minutes, I'm going to talk to  
**[00:14]** you about  
**[00:16]** considerations for making smarter MCP  
**[00:18]** servers. And in particular, we're  
**[00:21]** looking at context window problems.  
**[00:25]** And you may ask yourself, well, what is  
**[00:28]** that? So this is where an AI agent's  
**[00:33]** token limit is exceeded and that can  
**[00:36]** cause a number of symptoms. It's often  
**[00:39]** referred to as context rot.  
**[00:44]** And a contributor to this and I'll come  
**[00:47]** on to a bit more detail about context  
**[00:50]** windows is how we build MTP servers and  
**[00:55]** in particularly around tool definitions.  
**[01:00]** So this isn't something which is merely  
**[01:04]** theoretical.  
**[01:06]** If we look at a real world example here,  
**[01:08]** here's something which somebody posted  
**[01:11]** on Reddit  
**[01:13]** and they posed this question about  
**[01:16]** they'd looked at Claude code used the  
**[01:19]** Doctor utility which can show you tokens  
**[01:22]** consumption  
**[01:23]** and discovered they'd consumed 27,000  
**[01:27]** tokens before they'd even done anything.  
**[01:31]** And that all contributes towards the  
**[01:34]** context window filling up. And a context  
**[01:38]** window is essentially a term for  
**[01:41]** describing  
**[01:42]** all the things which your large language  
**[01:45]** model has to deal with.  
**[01:48]** And it also if we look beyond the  
**[01:51]** context window,  
**[01:53]** all those tokens are burning money.  
**[01:56]** And that's before you've actually done  
**[01:59]** anything with your MCP server and your  
**[02:02]** large language model.  
**[02:05]** And if we dig a bit more into what's  
**[02:08]** going on,  
**[02:10]** you can look at this particular picture.  
**[02:12]** And if we look at the top,  
**[02:15]** we can see what's going on here. When we  
**[02:18]** look at the interaction between the  
**[02:20]** model, the MCP client and server and one  
**[02:25]** of the first things that happens  
**[02:27]** is your MCP client will ask for the list  
**[02:31]** of tools which a MCP server has  
**[02:34]** available.  
**[02:36]** that tool list. So the name of the tool,  
**[02:39]** its definition description is processed  
**[02:43]** by the model and that consumes to uh  
**[02:46]** tokens and it takes up space in your  
**[02:49]** context window.  
**[02:51]** And like I've just mentioned, you  
**[02:53]** haven't actually done anything yet.  
**[02:56]** So  
**[02:58]** when we think about context and the  
**[03:01]** context window and how to have been used  
**[03:03]** here,  
**[03:05]** we need to take this into account when  
**[03:07]** we think about how we're designing our  
**[03:10]** MCP servers  
**[03:12]** and how we structure the tools an MTP  
**[03:16]** server has and how that server delivers  
**[03:20]** them. We now need to take that into  
**[03:23]** consideration along with everything else  
**[03:26]** you do when you're building an MTP  
**[03:28]** server like what communication protocol  
**[03:31]** are you going to use and you going to  
**[03:33]** use standard IO you going to use HTTP  
**[03:37]** are you going to use or you what I going  
**[03:39]** to do about logging now I have to think  
**[03:42]** about how can I optimize the  
**[03:44]** presentation of tools to the model so I  
**[03:48]** can optimize the token burn and I can  
**[03:50]** optimize the content text itself.  
**[03:53]** And when you're thinking about this, you  
**[03:55]** can roughly say for every single tool  
**[03:59]** definition you have,  
**[04:01]** it consumes 200 tokens.  
**[04:04]** And if you were  
**[04:06]** considering building an MCP server,  
**[04:09]** which was going to surface  
**[04:11]** a bunch of traditional REST APIs,  
**[04:15]** that could be multiple endpoints you're  
**[04:18]** presenting as tools. So maybe it could  
**[04:20]** be like 60 plus tools. So if you do the  
**[04:24]** math, that gives you around 12,000  
**[04:26]** tokens  
**[04:28]** right at the start of the conversation  
**[04:30]** between your MCP server and your model.  
**[04:36]** And that that tool count  
**[04:39]** matters, right? Because we've seen it  
**[04:41]** burns tokens. It impacts our contacts  
**[04:45]** window. And when MTP servers first  
**[04:49]** appeared, we all  
**[04:52]** kind of ran to get on board that  
**[04:53]** bandwagon and we just jumped straight  
**[04:56]** in, right? So we simply said, let's give  
**[04:58]** out all of our tools  
**[05:01]** because then  
**[05:03]** the model's aware of them, right?  
**[05:06]** So  
**[05:08]** by doing that in our haste, we kind of  
**[05:12]** looked before we well, we we forgot to  
**[05:15]** look before we left, right? So if we  
**[05:18]** take a moment and pause, you know, take  
**[05:20]** a deep breath and take a step back,  
**[05:24]** we need to consider what tools the model  
**[05:26]** needs to get a thing done.  
**[05:30]** And we need to try and avoid the model  
**[05:34]** drinking from a fire hose.  
**[05:37]** So, we need to think about how can we  
**[05:39]** give the model what it needs  
**[05:42]** whilst avoiding cluttering up with stuff  
**[05:45]** it doesn't need.  
**[05:48]** And here's where I'm going to talk about  
**[05:51]** three potential patterns you can  
**[05:53]** consider when you're looking at MCP  
**[05:55]** servers.  
**[05:57]** And they have trade-offs, right?  
**[05:59]** Nothing's for free.  
**[06:01]** So if we talk about the full list  
**[06:04]** approach which is what I just mentioned  
**[06:07]** where we give the model everything on  
**[06:10]** startup  
**[06:12]** and that's what the MCP specification  
**[06:16]** says happens.  
**[06:18]** So the client says give me give me the  
**[06:20]** tools the server responds with a tool  
**[06:22]** list. So we know it will always happen.  
**[06:24]** It's a reliable way of doing this but it  
**[06:28]** burns tokens. If we look to the far  
**[06:31]** right, then we can see what you could  
**[06:35]** describe as lazy loading.  
**[06:37]** So here we're giving the model the  
**[06:40]** ability to discover tools.  
**[06:43]** So the idea being that it finds the  
**[06:46]** tools that it needs, can ask more  
**[06:49]** questions about a tool, and then runs  
**[06:51]** it.  
**[06:53]** And then in the middle,  
**[06:56]** we're kind of trying to strike a middle  
**[06:59]** ground where we want to give the model  
**[07:03]** the tools that it's most likely to need  
**[07:06]** first  
**[07:08]** and then we'll also give it the ability  
**[07:11]** to find out more.  
**[07:14]** And one of the things we have to bear in  
**[07:16]** mind across all of these is a model  
**[07:21]** doesn't always do what you expect.  
**[07:25]** So it turns out it may not always ask.  
**[07:28]** So that's one of the things which you  
**[07:29]** need to bear in mind. So let's jump into  
**[07:33]** looking at each of these approaches in  
**[07:35]** turn. Let's start with the full list.  
**[07:42]** So this is guaranteed almost by the MCP  
**[07:45]** specification itself. According to  
**[07:48]** specification, when an MCP client starts  
**[07:51]** up, it always will ask an MCP server for  
**[07:55]** the tool list.  
**[07:57]** So you know that the model will be aware  
**[08:00]** of all of the tools but token usage,  
**[08:05]** right? And the context window. If we  
**[08:08]** scale this up to incorporate lots and  
**[08:11]** lots of tools, then we start to run into  
**[08:14]** some of those challenges.  
**[08:16]** But there are some things we can do  
**[08:19]** in terms of mitigation. And one of those  
**[08:22]** is to implement some kind of capability  
**[08:27]** uh capability filtering.  
**[08:29]** So we try and change the way we look at  
**[08:33]** the design of MCP server from how is the  
**[08:37]** model discovering tools to how can we  
**[08:41]** give the tools which are relevant  
**[08:45]** and one of the ways we can look at this  
**[08:48]** is to kind of look at filtering tool  
**[08:51]** sets as a product decision not just an  
**[08:54]** engineering one. So we can look at this  
**[08:59]** in terms of  
**[09:01]** at what point should we give the tools  
**[09:02]** out and how  
**[09:06]** do we go about doing that. So we can  
**[09:09]** look at it in terms of if I'm in a  
**[09:14]** development type environment then my MCP  
**[09:17]** server could expose tools for debugging  
**[09:20]** and to help me with development but  
**[09:22]** those tools would not appear in a  
**[09:24]** production environment because they're  
**[09:26]** not relevant.  
**[09:28]** We can also look at the role.  
**[09:31]** So the end user, if you like, who's  
**[09:34]** connecting  
**[09:35]** via our agent to this MCP server to get  
**[09:39]** a thing done, we can look at who they  
**[09:41]** are and see what they need and then give  
**[09:45]** them a subset of the overall tool list.  
**[09:49]** Um, for example, you could look at  
**[09:52]** scopes in a JWT  
**[09:54]** and based on that you could assign a  
**[09:57]** bunch of tools. We could also look at  
**[10:00]** the context. So for example, we could  
**[10:02]** decide that some tools you can always  
**[10:05]** use, but other tools are locked away  
**[10:08]** behind some form of authentication.  
**[10:11]** And there's a great example of this when  
**[10:13]** you go look at how GitHub has done it  
**[10:17]** and they allow for selecting of groups  
**[10:19]** of tools or individual one. So in that  
**[10:23]** particular example there  
**[10:26]** you can see that I'm asking for a subset  
**[10:29]** of the over overall list of tools which  
**[10:32]** GitHub can give me. So I'm calling out  
**[10:34]** specific ones but it also allows you to  
**[10:37]** to get hold of tools based on a category  
**[10:40]** as well. So that's an example of using  
**[10:43]** the full list but then filtering what  
**[10:46]** tools you get.  
**[10:49]** So the approach on the right hand side  
**[10:51]** from that diagram I showed you just a  
**[10:54]** few moments ago is to do what I would  
**[10:57]** describe as lazy loading.  
**[11:00]** So this is where you literally have  
**[11:01]** three tools  
**[11:03]** and the first tool allows the model to  
**[11:06]** discover what capabilities exist. So  
**[11:10]** it's literally asking the question what  
**[11:13]** can the MCP server do  
**[11:16]** and it will get a list of the tools by  
**[11:18]** name and you might give each tool a  
**[11:20]** brief description.  
**[11:22]** The model can then go for a particular  
**[11:25]** tool, ask the question, well, how does  
**[11:27]** this tool work?  
**[11:29]** And then based on that, it can then go  
**[11:31]** ahead and execute that tool.  
**[11:34]** And this, as you can see, there's only  
**[11:36]** three tools. So, it dramatically reduces  
**[11:39]** the context and dramatically reduces the  
**[11:43]** number of tokens.  
**[11:46]** But and there's always a but right with  
**[11:49]** lazy loading you are heavily relying on  
**[11:52]** a model  
**[11:54]** to follow what you to follow this  
**[11:57]** pattern of listing capabilities choosing  
**[12:01]** the right tool and then using it. You're  
**[12:04]** really at the whim of that model. And I  
**[12:07]** say in those terms because models can't  
**[12:11]** be compelled.  
**[12:14]** So um if you haven't come across that  
**[12:16]** yet um you will and you need to coach  
**[12:21]** and encourage and if you've ever dealt  
**[12:24]** with teenagers it's a very similar kind  
**[12:27]** of thing. Now there are some things you  
**[12:30]** can do around that in terms of you can  
**[12:32]** look into uh skills which can help  
**[12:35]** describe how a tool can be used and what  
**[12:38]** it can be used for but you're still  
**[12:40]** relying on that model to take that  
**[12:43]** advice  
**[12:45]** and we can see that where there are some  
**[12:49]** um occasions where we've actually seen  
**[12:52]** that with our MCP server which we have  
**[12:55]** for Neo4j  
**[12:57]** and that has the cap capability for a  
**[13:01]** model to discover what graph data  
**[13:03]** science tools, algorithms are available  
**[13:06]** for it to use. And what we've noticed is  
**[13:11]** if you phrase the question very  
**[13:14]** carefully,  
**[13:15]** then it will go ahead and use  
**[13:19]** that particular route where it discovers  
**[13:21]** the tool and then goes ahead and calls  
**[13:24]** the correct GDS algorithm.  
**[13:27]** But we've also frequently seen if you  
**[13:30]** don't phrase your question in that way  
**[13:33]** then the model will take the shortest  
**[13:36]** path available to it and I apologize for  
**[13:39]** that. There is no pun intended there and  
**[13:42]** it will take that path and would write  
**[13:45]** cipher  
**[13:46]** and that gives you a result but it's not  
**[13:49]** necessarily the best result. It's not  
**[13:52]** necessarily the best path for the model  
**[13:54]** to have taken, but it will do it.  
**[13:58]** And so you can see there where you  
**[14:01]** phrase the question so the model gets a  
**[14:05]** clear specific task.  
**[14:09]** You can see there where it will just try  
**[14:11]** and do it straight away or it will take  
**[14:13]** the easy path or it will infer the wrong  
**[14:16]** parameters to use.  
**[14:18]** And one thing just to be be aware of is  
**[14:21]** if you're going to go down this lazy  
**[14:23]** loading approach is it really depends on  
**[14:26]** how you're structured. So if you're  
**[14:28]** writing an agent working with a model,  
**[14:32]** you have more control over what's going  
**[14:34]** on  
**[14:36]** and that allows you to take advantage of  
**[14:38]** this type of approach. But if you've got  
**[14:41]** a public MCP server,  
**[14:44]** then this doesn't work spectacularly  
**[14:47]** well.  
**[14:49]** So the middle approach, the balanced  
**[14:52]** approach if you like when we looked at  
**[14:53]** that initial slide, this is where we've  
**[14:57]** got a graph sitting behind our MCP  
**[15:00]** server.  
**[15:02]** And here what we're doing is we're using  
**[15:06]** our knowledge we've encoded in our graph  
**[15:10]** to help with our registry of tools.  
**[15:14]** And one of the things we're doing is  
**[15:17]** taking advantage of the fact that graphs  
**[15:20]** are really good at answering questions  
**[15:23]** which a flat list cannot.  
**[15:26]** So here we can model the tools. We can  
**[15:30]** model them into categories.  
**[15:32]** We can record how often they're used. We  
**[15:36]** can look at how well they're used etc.  
**[15:39]** So kind of like usage data as well.  
**[15:43]** And the reason this is important is it  
**[15:47]** allows us to on that initial  
**[15:50]** tool call that tool list command which  
**[15:53]** the MCP client gives at startup is we  
**[15:57]** can give the model the common tools  
**[16:00]** first.  
**[16:03]** So for example, we could give it eight  
**[16:05]** commonly used tools and we know they're  
**[16:08]** commonly used because we've described  
**[16:10]** that in the graph which is supplying  
**[16:12]** that list of tools  
**[16:14]** and then we give the discoverable  
**[16:18]** tooling as well. So we allow the model  
**[16:22]** to find out more tools and we allow it  
**[16:24]** to do it by categories. So if you've got  
**[16:28]** tools which allow you to interact with a  
**[16:30]** database, you've probably grouped them  
**[16:34]** into things which may query your  
**[16:36]** database like readon tooling, tooling  
**[16:39]** that allows you to do imports, tooling  
**[16:41]** that allows you to do mutations, change  
**[16:43]** your data. So you can use that  
**[16:46]** information, those categories to group  
**[16:48]** that tooling together.  
**[16:51]** So here  
**[16:54]** we're ensuring that the model can't miss  
**[16:57]** what tools to start with, but also  
**[17:00]** because we're baking that discovery into  
**[17:02]** that initial tool list, the model is  
**[17:04]** aware of it. And the other thing we want  
**[17:06]** to do as part of our MCP server  
**[17:09]** functionality is every time a model uses  
**[17:12]** a tool, we're going to record that  
**[17:14]** usage. And so that allows us to when we  
**[17:18]** front up that initial common list,  
**[17:22]** that list is built off real world usage.  
**[17:26]** So we can ensure those commonly used  
**[17:30]** tools appear first  
**[17:32]** and then all the other stuff we make it  
**[17:34]** findable.  
**[17:37]** So if we look into a bit a bit more  
**[17:39]** detail about how this could look at the  
**[17:41]** back end, we've got a graph there and  
**[17:46]** we've got our gold node. They're  
**[17:49]** categories. So if I look at that  
**[17:51]** database example I just mentioned, that  
**[17:54]** could be queries, it could be mutations,  
**[17:56]** it could be importing. That's a  
**[17:58]** category. And then we've associated in  
**[18:02]** lavender  
**[18:03]** those are all the individual tools  
**[18:05]** associated with those categories. The  
**[18:07]** tool may belong to more than one  
**[18:08]** category, right? And this allows us  
**[18:11]** using cipher to find the common tools  
**[18:14]** based on usage  
**[18:16]** and that will be the initial list we  
**[18:18]** give out to the model and we could put a  
**[18:22]** limit on it. So we can say give me the  
**[18:24]** top 10, give me the top five, whatever  
**[18:26]** it may be. And then every time a tool is  
**[18:29]** being used, we're updating the graph so  
**[18:33]** that common tool list stays relevant.  
**[18:35]** It's based on what a model is being used  
**[18:38]** for. So here's here's an example. Um, so  
**[18:42]** if I was to create an MCP server for our  
**[18:46]** Aura API  
**[18:48]** and I could roughly model in an MCP  
**[18:52]** server the Aura API with 26 endpoints  
**[18:58]** or 26 tools if you like. And if I gave  
**[19:01]** that set of tools to the model every  
**[19:05]** time on startup, that would consume  
**[19:08]** approximately  
**[19:09]** just over 5,000 tokens.  
**[19:13]** But if I took the approach I've just  
**[19:16]** been talking about, I can look at my  
**[19:18]** usage data for the Aura API  
**[19:22]** and then I can use that data to say what  
**[19:25]** tools should I give initially those  
**[19:29]** commonly used tools. And I can see here  
**[19:32]** that  
**[19:33]** the top four  
**[19:35]** based on actual usage of the Aura API  
**[19:38]** are getting information about an Aura  
**[19:40]** instance, creating a snapshot, listing  
**[19:43]** all my or instances and then listing  
**[19:47]** information about the the tenants, the  
**[19:49]** projects which I have. So that top four,  
**[19:52]** that's my initial list. And then the  
**[19:55]** ones underneath it, they're the ones  
**[19:56]** which I'm going to start giving out when  
**[19:59]** the model asks for them. And if if I  
**[20:02]** take that approach for example, I list  
**[20:05]** out  
**[20:08]** eight commonly used tools. So I go for  
**[20:10]** those top eight for example, and then I  
**[20:12]** give two more. One's discovery, one is  
**[20:15]** execution.  
**[20:16]** Then I'm now down to approximately 2,000  
**[20:19]** tokens at startup. And that's roughly  
**[20:22]** about 62%  
**[20:25]** saved.  
**[20:26]** Right? So that's one one approach I  
**[20:30]** could take here.  
**[20:32]** And the thing to be aware of is what I'm  
**[20:35]** doing is the MCP server is storing its  
**[20:38]** tools  
**[20:40]** in in my graph.  
**[20:43]** So it doesn't have to necessarily be a  
**[20:46]** graph which I'm using with my MCB  
**[20:48]** server. It could be an entirely separate  
**[20:49]** one. And the tool list is living in the  
**[20:52]** graph itself and the tools are the  
**[20:53]** graph. And so you could imagine for  
**[20:58]** things like restful environments where  
**[21:00]** you want to front those with an MCP  
**[21:02]** server,  
**[21:04]** this is a great way of doing it because  
**[21:05]** you've got or likely to have usage  
**[21:08]** information about your REST endpoints  
**[21:11]** that can help you with that initial set  
**[21:12]** of common tools and then based on usage  
**[21:15]** you can adjust as needed.  
**[21:19]** And it's entirely possible that you  
**[21:21]** could bootstrap this. If you've got your  
**[21:24]** endpoints in an open API spec, you could  
**[21:27]** bootstrap from there.  
**[21:31]** So there's three possible approaches  
**[21:34]** here  
**[21:36]** and it really depends on your situation.  
**[21:39]** So if we consider  
**[21:43]** what scenario  
**[21:45]** you're in.  
**[21:47]** So we know from the NCP specification  
**[21:50]** itself  
**[21:52]** that it will always ask for the list of  
**[21:54]** tools. So I know that the full tool list  
**[21:57]** approach will always work. I've got  
**[22:00]** fairly good confidence because I'm  
**[22:01]** giving out that common batch of tools  
**[22:05]** with the graphbacked approach. That's  
**[22:07]** good as well.  
**[22:08]** um lazy loading like I've mentioned  
**[22:11]** before  
**[22:12]** you're relying on the model if I also  
**[22:15]** consider questions like reducing my  
**[22:17]** initial context is it deterministic will  
**[22:21]** it work with any type of client so by  
**[22:25]** that I'm talking about am I using  
**[22:27]** something like claw desktop or open API  
**[22:31]** chat GPT or am I writing my own agent  
**[22:35]** that's what I kind of need to consider  
**[22:38]** And then I also want to think about can  
**[22:40]** this adapt over time and adjust to  
**[22:43]** what's actually going on with the way my  
**[22:45]** MCP server has been used. And then  
**[22:48]** finally, will it scale? So those are  
**[22:50]** some of the questions you want to go ask  
**[22:52]** yourself and then you can see how each  
**[22:55]** of those approaches maps to those  
**[22:58]** questions.  
**[23:01]** And in in many ways  
**[23:05]** the question you're kind of not really  
**[23:07]** asking is which pattern. It's  
**[23:10]** understanding the tradeoffs. That's the  
**[23:12]** question you really need to look at. And  
**[23:15]** I've put in that text there, that black  
**[23:18]** box with that white text.  
**[23:21]** This is literally when I asked Claude  
**[23:24]** why it had taken a particular approach  
**[23:28]** and I wanted to understand why it hadn't  
**[23:30]** used some of the tools which it had  
**[23:33]** available to it in the MCP server I had  
**[23:36]** and Claude told me that you essentially  
**[23:39]** you cannot tell me what to do.  
**[23:43]** So it cooperates and it does so  
**[23:46]** voluntarily,  
**[23:48]** not because in my tool description I'd  
**[23:51]** used the word mandatory or I described  
**[23:54]** it as you must do this.  
**[23:57]** And so that's one of the things you need  
**[23:59]** to be aware of. So if you're writing the  
**[24:02]** agent, so I'm writing some kind of  
**[24:04]** chatbot for example,  
**[24:07]** then I've got much more control over  
**[24:09]** what's going on. And again, if you ask  
**[24:11]** Claude about what's the hierarchy it  
**[24:14]** uses to determine what it will do, the  
**[24:18]** ultimate determiner, if you like, right  
**[24:21]** at the top is anthropic itself,  
**[24:24]** then the agent, then the user. And so  
**[24:28]** that's how it decides if it's going to  
**[24:30]** do a thing. Ultimate control is with  
**[24:32]** anthropic. But if you're writing the  
**[24:34]** agent, you have a bit more control over  
**[24:36]** what's going on. And so in that  
**[24:38]** environment, you can use lazy loading if  
**[24:41]** you wish,  
**[24:42]** right? Because you have more control.  
**[24:45]** If you don't own the agent and you've  
**[24:49]** got no real idea who the clients could  
**[24:50]** be, so I'm hosting a publicly available  
**[24:54]** MCP server. Um, then I'm looking at  
**[24:59]** listing all the tools like doing that  
**[25:00]** full list.  
**[25:02]** I could also  
**[25:06]** look at the graphbacked approach in all  
**[25:09]** of these cases as well if I want to have  
**[25:11]** some kind of responsive MCP server that  
**[25:15]** almost gives the impression it's  
**[25:16]** learning over time. The other thing you  
**[25:19]** need to bear in mind is um go read what  
**[25:22]** the MCP spec says  
**[25:24]** and lean into that. There's no point in  
**[25:26]** trying to fight that.  
**[25:29]** leverage the fact that information is  
**[25:32]** always sent on startup like the tools  
**[25:34]** list call always happens  
**[25:37]** and then when you consider your MCP  
**[25:40]** server think about what the large  
**[25:43]** language model will see  
**[25:46]** and at what time it sees it and can you  
**[25:48]** do some controls around that.  
**[25:51]** So, those are some things, some  
**[25:53]** patterns, some thoughts,  
**[25:56]** things to consider when you're designing  
**[25:58]** your MCP server.  
**[26:01]** Um, so  
**[26:04]** I'd like to thank you for your your time  
**[26:06]** today. I've  
**[26:08]** um  
**[26:09]** >> I'm not quite sure how to help you with  
**[26:10]** that.  
**[26:12]** >> That's Alexa dropping in and prompting  
**[26:14]** me. Probably a classic example of  
**[26:16]** models. Um, thanks for your time. Um and  
**[26:20]** I shall  
**[26:22]** uh let me see if I can cover off some of  
**[26:24]** these questions in a couple of minutes  
**[26:25]** got left. Um the graph of tools  
**[26:27]** manually. Um so  
**[26:32]** with the example I gave I actually had  
**[26:36]** usage data coming from an API which was  
**[26:38]** in use today. So I could use that to  
**[26:42]** determine what my common tools would be.  
**[26:46]** Um if you haven't got that kind of  
**[26:48]** information then you can take an  
**[26:52]** educated guess of what those common  
**[26:54]** tools should be start with those and  
**[26:57]** then use the data you're getting back  
**[27:00]** from your MCP server which is updating  
**[27:03]** that graph which is recording that usage  
**[27:05]** to start to um trim and adjust that  
**[27:08]** list.  
**[27:10]** um the order of calling tools. Um yep,  
**[27:15]** that could vary. And that's another  
**[27:17]** thing you could start to bake into that  
**[27:20]** graph  
**[27:22]** and you could start recording in the  
**[27:24]** graph that models were using tool A and  
**[27:28]** then they'd go and use tool B and that  
**[27:32]** could help you categorize tools. But  
**[27:34]** then also in your tool descriptions, you  
**[27:37]** can tell the model that um to it's often  
**[27:41]** the case that tool A is is then called  
**[27:44]** and then tool to tool B follows it. So  
**[27:47]** you can bake that into the graph. You  
**[27:49]** can also bake that into the descriptions  
**[27:51]** which you give out with your tools um to  
**[27:54]** help educate your uh model on what to  
**[27:57]** do.  
**[27:58]** Um so again, thanks for your time today  
**[28:01]** and um enjoy the rest of the event.  