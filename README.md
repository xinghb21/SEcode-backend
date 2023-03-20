### 这是后端模板相关注意事项

添加应用的指令：

```
django-admin startapp [appName]
```

我已经创建好了`user`应用且填充了一个`startup`作为测试

添加应用后需要注意更改下面这些文件内容：

- `./Aplus/urls.py`，增加对应路由
- `./Aplus/settings.py` 中 `INSTALLED_APPS`
- `./sonar-project.properties`添加下面内容：
  - `sonar.source=[appName]`
  - `sonar.inclusions=[appName]/**/*.py`
  - `sonar.exclusions=[appName]/migrations/*.py`
- `start.sh`和`test.sh`，不知道现在有何影响

写好一个应用就可以把`board`删了