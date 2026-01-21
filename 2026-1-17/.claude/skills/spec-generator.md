# spec-generator

生成 42COG 格式的视频规约。

## 触发条件

- 用户要生成视频规约
- 用户要整理视频制作要求
- 完成策划后需要输出规约文档

## 输入

- 内容策划文档
- 视频脚本
- SEO 报告（可选）

## 规约格式

```xml
<spec>
  <section name="视频概述">
    <topic>主题描述</topic>
    <duration>目标时长</duration>
    <style>风格：教程型/故事型/评论型</style>
    <target_audience>目标受众</target_audience>
  </section>

  <section name="三事件结构">
    <event1>
      <title>事件1标题</title>
      <time>0:00-1:00</time>
      <content>引入问题/痛点</content>
    </event1>
    <event2>
      <title>事件2标题</title>
      <time>1:00-6:00</time>
      <content>展示解决方案</content>
    </event2>
    <event3>
      <title>事件3标题</title>
      <time>6:00-8:00</time>
      <content>总结升华</content>
    </event3>
    <meaning>观众收获</meaning>
  </section>

  <section name="SEO优化">
    <title>标题</title>
    <description>描述</description>
    <tags>标签列表</tags>
  </section>

  <section name="制作要求">
    <voiceover>配音要求</voiceover>
    <visuals>画面要求</visuals>
    <music>背景音乐</music>
    <subtitles>字幕要求</subtitles>
  </section>
</spec>
```

## 输出

- 规约文件：`.42cog/spec/pm/video_spec_{date}.md`
