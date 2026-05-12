# Transcript: https://www.youtube.com/watch?v=KJSHagHkX8I

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 656

---

**[00:09]** Hello everyone. Thank you so much for  
**[00:11]** joining us for our session. I'm here to  
**[00:13]** introduce our wonderful speaker Akil  
**[00:15]** Ham. And I'll go ahead and head over to  
**[00:16]** you.  
**[00:18]** >> Thanks Marie. Um hey everybody, how's it  
**[00:21]** going? Thank you so much for being here.  
**[00:23]** U today I want to talk to you about a  
**[00:25]** agentic graph. uh more specifically a  
**[00:28]** multi- aent approach of creating  
**[00:30]** knowledge graphs. This is something that  
**[00:32]** my team and I have developed as a  
**[00:34]** workflow uh because we've been doing a  
**[00:37]** lot of research and a lot of uh team  
**[00:39]** members are storing their data across  
**[00:42]** you know cloud folders and in their own  
**[00:44]** personal folders and there was no way  
**[00:46]** for us to find the data and look at what  
**[00:48]** we researching and so this tool is  
**[00:50]** something that we've created and it's  
**[00:52]** obviously evolving as we speak but I  
**[00:54]** wanted to share this with you uh get  
**[00:56]** your thoughts on it and you know  
**[00:58]** hopefully you can also implement this  
**[01:00]** within your teams as  
**[01:02]** So today's agenda I want to talk to you  
**[01:04]** about the current challenge that we're  
**[01:05]** facing the architecture overview um with  
**[01:09]** the data extraction strategies and  
**[01:11]** what's next because I think this is like  
**[01:14]** version two version two in this whole  
**[01:16]** app dev that we're doing and so this is  
**[01:19]** adding to like a broader vision  
**[01:21]** internally for our team and that's what  
**[01:23]** happens that's what I want to talk to  
**[01:24]** you about in what's next. So before we  
**[01:29]** begin, I always like to start off the  
**[01:30]** presentation by this famous quote by Fe  
**[01:33]** Lee. Uh artificial intelligence is not a  
**[01:36]** substitute for human intelligence. It is  
**[01:38]** a tool to amplify human creativity and  
**[01:41]** ingenuity. And this is something that I  
**[01:43]** always go back to as an anchor because  
**[01:46]** yes, AI is cool, but if it doesn't help  
**[01:48]** us do a uh improve our workflows or make  
**[01:52]** us more efficient, I feel like it's it's  
**[01:55]** it wouldn't be of no use to us, right?  
**[01:56]** So this is almost like a grounding  
**[01:58]** anchor.  
**[02:00]** Okay. So let's look at the current  
**[02:01]** challenge that this is again that's this  
**[02:04]** is what we're facing and I'm sure  
**[02:06]** different teams have different kinds of  
**[02:07]** problems that they're facing but this is  
**[02:08]** internal to us. And so the first one is  
**[02:11]** unstructured data right fragmented  
**[02:13]** storage. All of the research data lives  
**[02:16]** across multiple cloud folders and  
**[02:18]** personal drives. uh scattered notes. The  
**[02:21]** every researcher adds notes based off  
**[02:23]** the data that they've seen but they live  
**[02:25]** in that particular folder and so the  
**[02:28]** valuable insights kind of get buried. Uh  
**[02:30]** redundant effort and so if one team  
**[02:33]** member does some kind of research but  
**[02:35]** then the other team member would have to  
**[02:36]** look at the notes and may also have to  
**[02:38]** look at the data. So you're kind of you  
**[02:40]** know duplicating the work over and over  
**[02:41]** again and also disconnected context. uh  
**[02:45]** notes and datas are not linked together  
**[02:47]** and so it's hard to find which of the  
**[02:50]** research paper that the notes were made  
**[02:52]** from.  
**[02:54]** So just to give an example like every  
**[02:56]** researcher uploads and again this is  
**[02:59]** internally right. So we my team uh the  
**[03:02]** researcher uploads the data sets and  
**[03:04]** notes into separate folders and so as a  
**[03:07]** result of which the insights kind of  
**[03:09]** tied to the individual files stay tied  
**[03:12]** to the individual files and this makes  
**[03:14]** it difficult to connect the findings and  
**[03:16]** also to trace a single idea. you might  
**[03:18]** you almost have to go back through  
**[03:20]** multiple different research papers that  
**[03:22]** we would have read and not just research  
**[03:24]** papers you know like Excel files data  
**[03:26]** sets that we have we would have  
**[03:28]** initially combed through to get to this  
**[03:29]** point in the first place and and so when  
**[03:33]** every and and even though every  
**[03:35]** researcher would find relevant data but  
**[03:37]** they would save it in separate folders  
**[03:39]** just so they're trying to organize this  
**[03:41]** whole thing and so the notes and  
**[03:43]** observations are kind of stored in the  
**[03:45]** same folder as the data  
**[03:47]** and and over time each folder becomes  
**[03:50]** its own mini knowledge base because  
**[03:52]** you're kind of adding more notes to the  
**[03:54]** same folder. And so when the team meets  
**[03:57]** uh we discuss findings but the insights  
**[04:00]** kind of remain scattered across the  
**[04:02]** folders and so this is the current this  
**[04:04]** is the challenge that we were facing  
**[04:06]** when we started this whole process. uh  
**[04:09]** let's look at what the architecture that  
**[04:10]** we're proposing and so the architecture  
**[04:13]** that we're proposing and this is the  
**[04:15]** core of what we're proposing is we start  
**[04:17]** with user uploaded PDFs and it can be  
**[04:19]** any kind of data set you know PDFs  
**[04:21]** research papers uh you know Excel files  
**[04:24]** JSON tables JSON formatted tables you  
**[04:27]** know any kind of data set uh and that is  
**[04:30]** put through the pipeline and that's this  
**[04:32]** is the multi- aent pipeline where we  
**[04:34]** have four agents and one agent  
**[04:37]** identifies entities and relationships.  
**[04:40]** Uh the second one kind of extracts uh  
**[04:43]** the entities and relationships from the  
**[04:45]** data. Uh the third one merges them  
**[04:48]** because you know sometimes we have  
**[04:49]** duplicates when we're kind of chunking  
**[04:51]** the data across the board. And finally  
**[04:54]** the fourth one is a QC check which kind  
**[04:57]** of optimizes the graph before then being  
**[05:00]** pushed to Neoforj for persistence. And  
**[05:03]** finally, all of this is connected to a  
**[05:06]** chatbot. And in our case, we try we use  
**[05:08]** the latest um OpenAI chatkit with the  
**[05:12]** help of um Neoforj's MCP server to then  
**[05:16]** help us query the database based on the  
**[05:19]** research that we're doing. So this is uh  
**[05:22]** an overview of what we are using in our  
**[05:25]** app at least and that's what we're  
**[05:26]** proposing. In terms of the text stack,  
**[05:29]** uh this is this being a web app, we use  
**[05:31]** NexJS and TypeScript with Tailwind CSS  
**[05:34]** and chat and UI. The AI layer is GPD5.  
**[05:38]** Oh, before that I almost forgot. Uh all  
**[05:41]** of the multi- aents is is also wrapped  
**[05:44]** with lang tracing. So any kind of agent  
**[05:48]** that any kind of step that takes that is  
**[05:51]** taken by by an agent, we can even  
**[05:54]** evaluate it on the back end with the  
**[05:56]** help of LSmith. So that way um that way  
**[05:59]** we can control the output based on the  
**[06:02]** input that's coming in maybe change the  
**[06:04]** prompts of each of the agents to help  
**[06:06]** fine-tune it better. And so all of this  
**[06:09]** is uh wrapped with lang tracing  
**[06:12]** and and so the data layer in the text  
**[06:15]** stack is neoforj.  
**[06:17]** So now that we've looked at the current  
**[06:19]** challenge and we've looked at the  
**[06:21]** architecture that we're proposing, let's  
**[06:23]** uh dig a little bit deeper, right? Let's  
**[06:25]** look at the solution. So this is how the  
**[06:28]** web app looks like for us wherein you  
**[06:31]** have uh wherein the researchers can drop  
**[06:34]** in their PDFs of any kind of data sets.  
**[06:36]** They can either define what they're  
**[06:38]** studying to get an AI suggested list of  
**[06:41]** entities and relationships or we can or  
**[06:44]** the user can define their own entities  
**[06:46]** and relationships that they want to that  
**[06:49]** they want the agents to look for in the  
**[06:51]** data. uh and then finally you can  
**[06:54]** process this and then the after which we  
**[06:57]** can look at what the graph looks like on  
**[07:00]** Neo 4j.  
**[07:02]** So the first step in this whole process  
**[07:04]** is user input. In this the researchers  
**[07:07]** uploads the documents or data sets into  
**[07:09]** the system. uh they define what kind of  
**[07:12]** information that they want to extract  
**[07:14]** entities concepts right uh or  
**[07:16]** relationships and AI and so there so  
**[07:19]** there are two options that we added into  
**[07:21]** this whole thing which is one we as a  
**[07:24]** user can define the entities and  
**[07:26]** relationships that we're looking for or  
**[07:29]** we can you know define the area of  
**[07:31]** research and give it to the AI analyzer  
**[07:34]** which will then suggest some nodes and  
**[07:37]** entities but the first step starts with  
**[07:40]** adding database adding data to the  
**[07:42]** database. So the idea is that the more  
**[07:45]** we do research on a particular domain  
**[07:48]** and the more data we accumulate all of  
**[07:50]** that can be dropped into this particular  
**[07:53]** web app and so the graph keeps expanding  
**[07:56]** based on what we're researching. So  
**[07:58]** they're all living in one location.  
**[08:02]** So the a one of the agents and the first  
**[08:05]** agent is an analyzer agent which is when  
**[08:09]** the user puts the PDF or any data set  
**[08:11]** inside they can either rely on what the  
**[08:15]** agent thinks should be the entities and  
**[08:17]** relationships. So they can put in what  
**[08:20]** the research focus focuses and get AI  
**[08:23]** suggestions. uh in this there were there  
**[08:26]** were two ways or two directions that we  
**[08:28]** could have gone in this particular uh in  
**[08:30]** this particular agentic approach was we  
**[08:33]** could have taken the data that's been  
**[08:36]** uploaded by the user and then taken the  
**[08:39]** suggestion uh taken the research focus  
**[08:41]** and then made the AI to compare like  
**[08:44]** look into the data and then suggest the  
**[08:46]** LMS but we felt that was a little bit  
**[08:49]** redundant just in this uh initial  
**[08:52]** versions of the app. So what we're doing  
**[08:54]** in this case is just we're just defining  
**[08:56]** the uh research focus or the area of  
**[08:58]** focus that we're looking into and based  
**[09:01]** off of that you have the LM that or the  
**[09:03]** agent that is uh you know suggesting  
**[09:06]** entities and relationships.  
**[09:08]** So in this case you can tell that this  
**[09:11]** was for an example I put in the latest  
**[09:15]** uh research paper that was released by  
**[09:17]** Apple on the and that was called the  
**[09:20]** pico banana 400k  
**[09:23]** and so I asked AI to suggest some  
**[09:26]** entities and relationships and you can  
**[09:28]** see on the right you have the entity  
**[09:30]** types and you have the relationship  
**[09:31]** types and all we have to do is select  
**[09:34]** which ones we want or we can also add  
**[09:36]** custom entity types and relationships.  
**[09:38]** at the bottom.  
**[09:40]** >> So now that we have you know put in the  
**[09:43]** data and then we have also gotten the  
**[09:46]** entity types and relationships some of  
**[09:48]** them are suggested by AI some you know  
**[09:51]** by the user we go on to the next step  
**[09:53]** which is oh before that uh just to give  
**[09:57]** a idea or just to give a code snippet of  
**[10:00]** what the agent looks like. So we're we  
**[10:03]** we're doing the passing um function for  
**[10:06]** the open AIS API where the output is  
**[10:09]** going to be a JSON output and that is  
**[10:12]** obviously that is defined with Zord. So  
**[10:15]** agent one analyzes the research focus  
**[10:18]** and suggests domain specific entry and  
**[10:20]** relationship types. Uh the researchers  
**[10:22]** can then select modify or add any kinds  
**[10:25]** of new entities and relationships. Uh  
**[10:27]** some of the examples for this particular  
**[10:30]** research paper was image edit  
**[10:32]** instruction data set subset and the  
**[10:34]** relationships was has edit instructions  
**[10:37]** are generated by this is just an example  
**[10:40]** uh use case but obviously you can add  
**[10:42]** your own um entities and relationships  
**[10:47]** u to and then we al like I mentioned  
**[10:49]** earlier we have lang tracing for eval so  
**[10:53]** every agent  
**[10:55]** behavior is fully observable through  
**[10:56]** lang Thanks for we can trace every LM  
**[10:59]** call from the system and the user  
**[11:01]** prompts to the structured response along  
**[11:03]** with runtime metrics. So this kind of  
**[11:05]** helps us validate the accuracy, compare  
**[11:09]** prompt iterations and ensure the  
**[11:11]** pipeline stays consistent as we scale  
**[11:13]** across different research areas. Right?  
**[11:16]** So as you can tell with the image on the  
**[11:18]** right, that is the um that is the  
**[11:22]** backend eval that we looking at. And so  
**[11:25]** the output B it also gives you reasoning  
**[11:28]** and that's based on the ZOD kind of  
**[11:30]** definition that we put in. So we wanted  
**[11:32]** entities we wanted relationships and  
**[11:34]** also we wanted the reasoning as to why  
**[11:37]** this was used why these were selected  
**[11:39]** from that particular area of research.  
**[11:42]** Again just as to eval so that if we  
**[11:45]** don't like the way it's been done we can  
**[11:47]** go back in and change the prompts and  
**[11:50]** you know look at it again.  
**[11:53]** So, so now we have put in the data. Uh,  
**[11:56]** we've chosen the entities and  
**[11:58]** relationships. We've also used the one  
**[12:01]** of the agent ones analyzer to give us  
**[12:03]** some examples and ideas of what we  
**[12:06]** should also look for look in the data  
**[12:08]** set for.  
**[12:10]** So the next agent is the extractor agent  
**[12:13]** which wherein we take the documents we  
**[12:16]** chunk them and then we compare the  
**[12:18]** entity types that we have chosen in step  
**[12:21]** one to what is present in all of these  
**[12:24]** in in the research paper. I'll tell you  
**[12:26]** more about it. So in this agent  
**[12:29]** essentially splits each document into  
**[12:31]** smaller check text  
**[12:33]** chunks for parallel processing. Uh so it  
**[12:37]** applies the schema suggested by agent  
**[12:39]** one or you know the custom schema that  
**[12:42]** the user suggested and extracts  
**[12:44]** information from each chunk  
**[12:45]** independently and simultaneously. So all  
**[12:47]** of these chunks are being processed  
**[12:49]** parallelly and so this produces a  
**[12:51]** structured output of entities and  
**[12:53]** relationships from each chunk.  
**[12:57]** And what that means is uh so in the  
**[13:00]** first in the first step we selected  
**[13:02]** these were the selected nodes right  
**[13:04]** image edit instruction edit pair and  
**[13:06]** edit operation type and some of the  
**[13:08]** relationships that were that came out of  
**[13:10]** a step one with agent one was has edit  
**[13:14]** instruction has edit type um and also  
**[13:19]** part of so now it essentially takes the  
**[13:22]** chunks in this case the PDF that I put  
**[13:25]** in the research paper was divided  
**[13:26]** divided into five chunks of 8,000  
**[13:29]** characters and it takes each chunk and  
**[13:31]** then finds out the node with the type.  
**[13:34]** So for example on the right side you can  
**[13:36]** see with it it found out the ID uh the  
**[13:40]** type is edit instruction and the  
**[13:42]** properties. So it's essentially taking  
**[13:44]** the type uh the entity type that we want  
**[13:47]** to look for and it's finding similar  
**[13:50]** content and it's creating a node out of  
**[13:52]** it. And same thing with relationships.  
**[13:54]** It took the relationship in this case  
**[13:56]** the type is has edit instruction and it  
**[13:59]** found the target found the source and it  
**[14:01]** found the properties. So essentially  
**[14:04]** we're kind of finding we're creating  
**[14:06]** relationships and also entities around  
**[14:08]** the around our entities and  
**[14:11]** relationships that we want to based off  
**[14:14]** where we want to find that we want to  
**[14:16]** research based off our area of focus.  
**[14:21]** Um and so the co the code snippet for  
**[14:24]** this for this agent is uh essentially  
**[14:27]** this wherein the GPD5 extracts entities  
**[14:30]** and relationships. Uh another thing that  
**[14:32]** in the code as you can tell this entire  
**[14:35]** agent is wrapped with the traceable  
**[14:37]** function and that's how we can you know  
**[14:39]** trace all of these agentic appro agentic  
**[14:42]** steps that it takes every single time.  
**[14:45]** Um and so the prompts and the model with  
**[14:48]** strict guidelines to minimize duplicates  
**[14:51]** output structured objects notes to  
**[14:54]** entities uh relationships links between  
**[14:57]** entities  
**[14:59]** and so this is the example of this  
**[15:01]** agent's uh evaluation that's happening  
**[15:04]** in the back end. So we can debug each  
**[15:06]** process chunk to confirm that the  
**[15:08]** correct nodes and relationships were uh  
**[15:11]** relationships were  
**[15:14]** relationships were extracted. Uh we can  
**[15:16]** validate the properties and the types of  
**[15:18]** each entity directly from the trace  
**[15:20]** output and it provides full visibility  
**[15:22]** into each LM's call including the input  
**[15:25]** text, the schema and the output. as and  
**[15:28]** as you can tell in the image we have I  
**[15:30]** think this is we are looking at um we're  
**[15:33]** looking at relationships in this case  
**[15:35]** and so you have the source you have the  
**[15:37]** target you have the relationship type  
**[15:39]** and you have a little bit of a  
**[15:40]** description to give us the context of  
**[15:43]** what this uh whole whole entity and  
**[15:46]** relationship was.  
**[15:48]** So now that we've gone through five uh  
**[15:51]** five chunks and which this kind of gives  
**[15:54]** about similar entities and relationships  
**[15:58]** across each chunk but now we want to  
**[16:00]** kind of merge them obviously with  
**[16:02]** reasoning but also merge them to remove  
**[16:05]** dup any kind of duplicates and  
**[16:07]** consolidate the whole list and that  
**[16:09]** happens with the entity merger that  
**[16:12]** happens with the entity merger agent.  
**[16:13]** And so in this case in this the agent  
**[16:16]** consolidates any kind of duplicate  
**[16:18]** entities using LLM based re reasoning  
**[16:22]** instead of string matching. So we're  
**[16:24]** just not matching the text of the input  
**[16:27]** schema uh text of the entities and  
**[16:30]** relationship across the five chunks. We  
**[16:32]** are essentially taking the description  
**[16:34]** that it came with that it comes with and  
**[16:37]** the LLM is essentially reasoning as to  
**[16:39]** see if they both are along the same  
**[16:41]** lines. If yes, then they're merged. So  
**[16:44]** from these from the five chunks, we got  
**[16:47]** about 84 entities. Uh just to give an  
**[16:49]** example, edit instructions, you had AC,  
**[16:52]** AC++, instruct picks to pick and  
**[16:55]** instruct edit, edit pairs,  
**[16:59]** uh and also edit operation type. So like  
**[17:01]** these had almost similar reasoning and  
**[17:04]** so it kind of you know merged all of  
**[17:07]** these. it merged whatever it thought was  
**[17:10]** similar and it came down to 32  
**[17:13]** dduplicated entries.  
**[17:16]** Uh just to give an example and to give  
**[17:18]** an example of what the code looks like  
**[17:19]** again this is also wrapped with a  
**[17:22]** traceable function from languid and so  
**[17:24]** it groups all the extracted entities by  
**[17:26]** type and each group is then sent to the  
**[17:30]** agent to do semantic dduplication based  
**[17:33]** on meaning and formality. Uh the LLM  
**[17:36]** also identify variations that refer to  
**[17:39]** the same real world entity and it maps  
**[17:42]** duplicate names to a canonical entity  
**[17:45]** name. Right? And all of this gets is  
**[17:48]** defined in this um in the with the  
**[17:50]** within the agent as an instruction. And  
**[17:53]** finally this is what the lang tracing  
**[17:56]** looks like. And so the trace shows how  
**[17:58]** agent 3 merged all the duplicate  
**[18:01]** entities. Now we can now open any merge  
**[18:04]** call that has happened, review the raw  
**[18:05]** inputs and the canonical outputs and  
**[18:08]** even read the LLM's reasoning as to why  
**[18:11]** these entities were combined. And the  
**[18:14]** reasoning again is obtained based off of  
**[18:16]** the Zod schema that we have defined. Uh  
**[18:20]** because again we want to know we want to  
**[18:22]** eval. And another thing that I forgot to  
**[18:26]** um explain before was in this whole  
**[18:29]** process of building this solution for  
**[18:32]** our team. I think eval was the top  
**[18:36]** priority. Yes, we could have built  
**[18:38]** without it. But without having any kinds  
**[18:41]** of eval the research team couldn't have  
**[18:43]** actually looked at how good the output  
**[18:46]** was and compared it to what their output  
**[18:49]** was when they did it without this app  
**[18:51]** before when the app existed. So eval is  
**[18:54]** I feel like the bedrock of any uh AI  
**[18:56]** solution that is that needs to be built  
**[18:58]** out there.  
**[19:01]** And so now we've gone through the four  
**[19:04]** agents, right? The three agents and then  
**[19:06]** the fourth agent and the final one is an  
**[19:08]** optimizer which essentially validates  
**[19:11]** and optimizes the graph quality.  
**[19:14]** So agent 4 is a semantic QA quality  
**[19:17]** assessment pass. It removes three  
**[19:20]** relationships. It in this case it  
**[19:22]** removed three relationships that were  
**[19:24]** either reversed or were using the wrong  
**[19:26]** word. So it kind of looks at grammatical  
**[19:28]** errors. It looks at the description. It  
**[19:31]** looks at everything and finds  
**[19:33]** similarities and and suggests that these  
**[19:36]** things need to be removed because you  
**[19:38]** know uh it has its own set of reasoning.  
**[19:40]** And so for example in this particular  
**[19:43]** run that we did it removed three  
**[19:45]** relationships which is Gemini's 2.5 Pro  
**[19:48]** produced by model and nanobanana it was  
**[19:51]** likely redundant and the reasoning is is  
**[19:54]** what it says was likely reversed or  
**[19:56]** redundant evaluation is not equal to  
**[19:58]** production. Then nano banana applies  
**[20:01]** edit operation to an MLM based quality  
**[20:04]** scoring. This is a semantic mismatch.  
**[20:07]** Quality scoring is an assessment method,  
**[20:10]** not an edit op. So I don't know if you  
**[20:12]** remember in the beginning we wanted to  
**[20:15]** look for erit uh operations and so it it  
**[20:19]** still took the initial entities and  
**[20:22]** relationships that we defined and it's  
**[20:24]** you know bringing into this and then uh  
**[20:26]** optimizing this even more based off of  
**[20:28]** our initial  
**[20:31]** entities and relationships that we've  
**[20:33]** defined. Uh and so the last one was and  
**[20:36]** only relationships were removed. None of  
**[20:38]** the nodes were removed in this whole  
**[20:39]** process.  
**[20:42]** So agent 4 is essentially the graph  
**[20:45]** quality auditor. It samples parts of the  
**[20:47]** graph, asks the GPD, asks the agent to  
**[20:51]** flag vague or inconsistent relationships  
**[20:53]** in comparison to the defined entities  
**[20:57]** and relationships from step one and  
**[20:59]** removes only those with lower  
**[21:00]** confidence.  
**[21:02]** Uh the goal is to not delete data but to  
**[21:05]** improve semantic precision keeping the  
**[21:07]** final graph lean and meaningful before  
**[21:10]** saving it to neo4j.  
**[21:14]** Um so again this is also wrapped with  
**[21:17]** the lang traceable and so in this we can  
**[21:20]** look at the trace for the final event.  
**[21:24]** So every optimization call is recorded  
**[21:26]** including what data was sampled and what  
**[21:29]** issues were flagged and the reasoning  
**[21:31]** behind each decision. So this means  
**[21:33]** every relationship removal or node  
**[21:37]** adjustment can be traced, reviewed and  
**[21:40]** even replayed and that's the beauty of  
**[21:42]** Langmith. So the level of transparency  
**[21:45]** gives us the confidence that based on  
**[21:48]** what research papers or research data we  
**[21:51]** put in based on what entities and  
**[21:53]** relationships we define that the output  
**[21:58]** that came about was what we needed and  
**[22:02]** and I'm not saying it's 100% accurate  
**[22:04]** always but with the help of eval and you  
**[22:08]** know us fine-tuning the prompt for each  
**[22:10]** of the agents it kind of gets us closer  
**[22:14]** to being 100%. We only need a little bit  
**[22:17]** of, you know, little bit of time and  
**[22:19]** effort in the end to now massage the  
**[22:21]** research that we're doing. And that's  
**[22:23]** that's all possible. was only possible  
**[22:25]** with the help of Langmith's evals  
**[22:30]** and  
**[22:33]** yeah  
**[22:35]** so once once we've once we've you know  
**[22:38]** gone through all the bases which is  
**[22:40]** starting with the whole PDF entities and  
**[22:43]** pushing it through  
**[22:46]** all the four agents we finally have to  
**[22:48]** push it to Neoforj for persistence and  
**[22:51]** so in this case  
**[22:53]** everything we we have extracted is  
**[22:54]** cleaned and then it's written into the  
**[22:57]** Neoforja database. Uh in this case we've  
**[23:00]** used the batch unwind pattern. One query  
**[23:04]** creates all nodes and other groups with  
**[23:07]** relationships by type. So this kind of  
**[23:10]** is almost 10 times faster than the  
**[23:12]** standard inserts uh thanks to merge and  
**[23:15]** flexible enough to handle the dynamic  
**[23:18]** schema definitions.  
**[23:20]** So just in this particular example the  
**[23:24]** write time was about 2 seconds. Uh total  
**[23:28]** there were about 57 nodes that were put  
**[23:30]** in 179 relationships four distinct  
**[23:33]** relationship types for each of those  
**[23:35]** nodes. Uh the right pattern was like I  
**[23:38]** mentioned batch unwind plus merge and it  
**[23:41]** was successfully stored to Neo4j. So and  
**[23:45]** each relationship type is also grouped  
**[23:47]** for performance. So that makes it faster  
**[23:50]** while while in this whole process.  
**[23:54]** Um so just to give an example of what  
**[23:57]** the code looks like for this for this  
**[23:59]** final step is it writes all the nodes  
**[24:02]** and relationships to Neoforj when uh in  
**[24:04]** batch using the unwind plus merge but  
**[24:07]** merge pattern groups relationships by  
**[24:09]** types and this is the types uh that we  
**[24:12]** we had you know uh we had put it in the  
**[24:16]** put in the step one entities and  
**[24:19]** relationships. So those are those are  
**[24:21]** called those are what we define as types  
**[24:23]** and based off of the types it's it you  
**[24:26]** know groups the relationships and  
**[24:27]** entities and then pushes it into  
**[24:30]** neoforj.  
**[24:32]** Uh each relationship type is written in  
**[24:34]** its own cipher query for like parallel  
**[24:36]** efficiency  
**[24:37]** and automatically sanitizes userdefined  
**[24:40]** relationship names. So like uppercase  
**[24:42]** special characters and also a replace.  
**[24:47]** And so now this kind of gives us the  
**[24:50]** opportunity to then use cipher query  
**[24:52]** from the chatkit or any chatbot with the  
**[24:55]** help of MCP server for us to query all  
**[24:57]** of the data and the research that we've  
**[25:00]** done. And the final step is you know we  
**[25:04]** kind of hook it up to the chatkit  
**[25:08]** with the help of Neoforj MCP server and  
**[25:12]** that's how um and then we start asking  
**[25:14]** questions. So essentially what we've  
**[25:18]** created is our version of a internal  
**[25:22]** assistant that just takes all the data  
**[25:25]** in but not all the data from the  
**[25:27]** internet more so um the data that we  
**[25:31]** deem necessary for a particular research  
**[25:33]** that we're doing. So this instant kind  
**[25:36]** of uh exists for different types of  
**[25:38]** research that happens in different  
**[25:40]** domains.  
**[25:42]** So what's next? So what's next? We have  
**[25:46]** a couple of steps that we're looking to  
**[25:48]** help improve this process even better is  
**[25:52]** domain agnostic. The same work uh work  
**[25:54]** the same architecture works across any  
**[25:57]** research domain and that I think comes  
**[25:59]** from kind of looking at the types of um  
**[26:03]** looking at types of prompts and how can  
**[26:06]** we make the prompts better. But that's  
**[26:08]** just step one. I think step two is also  
**[26:11]** injecting while it's analyzing while the  
**[26:15]** agents are doing injecting some  
**[26:17]** instructions  
**[26:19]** similar to how clock code has come up  
**[26:21]** with their skills.mmd. So this is  
**[26:24]** another step that we are planning to add  
**[26:26]** wherein each agent has its own version  
**[26:29]** of rag which it can then look at look at  
**[26:31]** the things that it needs to dig into and  
**[26:34]** then does the you know entity extraction  
**[26:38]** merging and optimizing  
**[26:41]** uh graph analytics I don't think we've  
**[26:43]** pushed how much of neoforj is being used  
**[26:45]** in this uh for now it's it's a great way  
**[26:48]** to build the knowledge graph but I think  
**[26:51]** we want to push it more in terms of data  
**[26:54]** science algos,  
**[26:56]** page ranking, community deduction, uh  
**[26:59]** link prediction and similarities across  
**[27:02]** the nodes and relationships.  
**[27:04]** Uh multimodal extraction, that's a big  
**[27:06]** thing that we're looking into. Right  
**[27:08]** now,  
**[27:10]** it just does text and a little bit of  
**[27:12]** tables, right? But we want to be able to  
**[27:13]** bring in images, videos and uh and make  
**[27:17]** it multimodal in terms of extracting the  
**[27:19]** data u and so and also real-time  
**[27:22]** pipeline. This is real time to a certain  
**[27:25]** extent, but we want to give this uh we  
**[27:30]** want to give this workflow the ability  
**[27:32]** to just keep ingesting not just the not  
**[27:34]** just the people or the users putting in  
**[27:36]** the data but also while we're querying  
**[27:39]** we can do a query onto the internet and  
**[27:41]** that data goes in as well and the graph  
**[27:44]** just keeps updating based on the guard  
**[27:46]** rails that we have  
**[27:49]** uh defined going Okay.  
**[27:52]** Um, and so I want to end this and if you  
**[27:56]** have any questions, please uh  
**[28:01]** you can enter it in the message box  
**[28:07]** and hopefully I can answer some of the  
**[28:10]** questions  
**[28:18]** or if you think of anything Um,  
**[28:22]** you can hit me up. This is my website.  
**[28:26]** Uh, you can find me on LinkedIn and then  
**[28:28]** I can help answer any of the questions  
**[28:29]** that you you may come across later on.  