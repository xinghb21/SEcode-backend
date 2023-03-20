# 工作手册

## 项目介绍

企业固定资产管理系统，本项目是一个经典的前后端对接加数据库持久储存的项目，大部分需求也是经典的增删改查，具体的需求希望大家详细阅读大作业对应文档，对于文档中需求需要自定义的地方，请大家在微信工作群中提出，收到反馈后再添加到项目的飞书文档中。

## 需要滴工作栈

### 团队开发——git

首先可以对于git的基本概念可以参考[Git教程 - 廖雪峰的官方网站 (liaoxuefeng.com)](https://www.liaoxuefeng.com/wiki/896043488029600)这篇中文教程，写得还可以，比较易懂。后续部分内容还可以参考github的官方文档[GitHub Documentation](https://docs.github.com/en/)

### 前端开发

react框架

nginx配置

前端ui设计（善于使用搜索引擎找到适合的轮子）

API文档的初步设计

### 后端开发

数据库设计

Django

按照api文档进行前后端通信逻辑完善

### 自动化测试

CI\CD

单元测试

## 工作规范

### 项目开发概念介绍

在本次项目中，我们一共会经历4次迭代周期(iteration)，需要实现若干需求文档中的原始需求(IR),对于其中若干个IR，我们会进行实现分析，最终拆解为若干个SR并以issue的形式分配给具体的开发人员，注意每个SR需要具体可操作，一个SR对应一个issue。

IR命名规范：IR.id

本项⽬的 SR 命名类似于 SR.Iteration.SR_Task.SR_id

▪ 其中 Iteration 为当前对应迭代周期,使用阿拉伯数字，为1-4的整数，但请记为001

▪ SR_Task 中：

• 0 对应项⽬脚⼿架类⼯作

• 1 对应项⽬前端相关开发⼯作，如 ui, style, logic

• 6 对应项⽬后端相关开发⼯作，如 model, api, crontab, logic

• 9 对应项⽬ Bug 修复⼯作

SR_id为一个自增的正整数，用于区别同一迭代周期同一性质的不同service requirement

一个正确的SR命名类似：SR.001.9.001

⼀个 Service 是⼀些具有特定功能的 SR 的集合

在某种程度上，Service 和 IR 都是评估项⽬完成进度的⽅式

但是，Service 更加偏向于项⽬的模块化开发进度，⽽ IR 则是偏向于单个需求的开发进度

本项⽬中，我们共有以下三种服务需要实现（目前只想到三种）：

UMS：⽤⼾管理服务，这个模块主要负责⽤⼾的登录，注册，⾝份验证

BPM：业务人员管理，这个模块负责实现业务实体和各种人员之间的交互和管理

BAM：业务资产管理，这个模块主要负责各种人员（主要是资产管理员）对资产的管理

### Issue发布规范

每次 Issue 发布时，其标题定为 “[SR名称]需求表述”

每个 Issue 仅对应⼀个 SR，进⽽仅对应⼀个 Service，其内容应具体⽽可测试

被分配到任务的负责⼈应及时在 Issue 中使⽤ “评论” 跟进进度

### Branching 规范：

#### 关于 master 分⽀

仅有项⽬的总维护者有权限接触到 master 分⽀

除 init commit 之外，禁⽌直接向 master 分⽀推送 commit

项⽬总维护者负责 Pull Request 的 review 与 merge

需要加⼊ CD 功能，实现版本的即时更新

#### 关于 dev 分⽀

分项⽬的管理员有权限直接向 dev 分⽀上推送非更改

分项⽬的管理员有权限决定是否合并其他 feature 分⽀到 dev 分⽀

当分项⽬的管理员认为需要进⾏版本迭代之时，提请 Pull Request 到 master 分⽀

需要加⼊ CI 功能，以便进⾏代码检查与单元测试

#### 关于 feature-* 分⽀

feature分支命名规范：feature-SR名称

较为模块化的新功能开发需要从 dev 分⽀新建 feature-* 分⽀

在特性开发完毕后，开发者提请 Pull Request 到 dev 分⽀

分项⽬管理员在进⾏ Code Review 之后决定是否合并分⽀到 dev 中

需要加⼊ CI 功能，以便进⾏代码检查与单元测试

#### 关于 hotfix-* 分⽀

当项⽬在运⾏状态中出现严重 bug 时，需要从 master 分⽀建⽴ hotfix 分⽀对其进⾏热修复

### Commit 规范

在本项⽬中，采⽤ Commit Message 标题中 /[SR.\d{3}.\d{1}.\d{3}(.[I/F/B])?]/ 的匹配模式来决定Commit 是否有 SR 关联

在本项⽬中，.I .F .B 分别为 wIp, Finalize, Bugfix 的缩写，分别对应特性的中间 Commit，特性的 Merge Request，特性的 Bugfix，为可选项。

•在本项⽬中，在开发新特性 SR.001.1.001 时，⼀般地你需要进⾏如下操作：

`git checkout -b feature-SR.001.1.001`

然后进⾏代码修改，在本地通过 lint 测试与 test:unit 测试，排除掉本⼈可以排除的 bug

`git add .`

`git commit -m [SR.001.1.001.I] 描述信息 (#Issue号)`

`git push origin feature-SR.001.1.001`

在这里请一定注意commit要与issue和SR相关联。

#### Pull Request 规范

在本项⽬中，采⽤ Pull Request 标题中 /[SR.\d{3}.\d{1}.\d{3}(.[I/F/B])?]/ 的匹配模式来决定 Pull Request 是否有 SR 关联

在本项⽬中，.I .F .B 分别为 wIp, Finalize, Bugfix 的缩写，分别对应特性的 中间 Commit，特性的 Merge Request，特性的 Bugfix，为可选项。

在本项⽬中，在请求合并新特性 SR.001.1.001 时，⼀般地你需要进⾏如下操作：

开发并 push 新特性到 GitLab

选择新建 Pull Request 到 dev 分⽀

◦ 注意：你必须通过 test CI 测试后才有可能被合并

标题为 `[SR.001.1.001.F] 描述信息 (#任务 Issue 号)`

在 Code Review 之后，你的 PR 便会被项⽬负责⼈合并