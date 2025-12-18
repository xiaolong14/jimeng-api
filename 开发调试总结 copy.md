视频测试：
生成视频似乎不限制并发，我可以一个账号同时生成多个视频
一个账号的额度，一天有大概能支持两次生成视频的机会，隔天刷新额度
基于：jimeng-video-3.0模型测试
并且视频生成会出现站点问题：
us-sesionid美国站点我发现就容易出现下列错误：
{
    "code": -2008,
    "message": "视频生成失败，状态码: 30，错误码: 1500",
    "data": null
}

只需要将站点切换为：
hk，jp，sg 直到全部切换完成都无法完成才是真正的失败



出现这个响应也代表请求彻底失败，这是账号速率限制，代表生成视频的次数消耗殆尽
{
    "code": -2001,
    "message": "[请求失败]: api rate limit (错误码: 1)",
    "data": null
}


出现这个响应也代表请求彻底失败，这是账号积分不足以生成视频或图片了
{
    "code": -2001,
    "message": "[请求失败]: 积分不足 (错误码: 1006)",
    "data": null
}




成功响应：
{
    "created": 1765861252,
    "data": [
        {
            "url": "https://v16-cc.capcut.com/1afbbcf38412c8addb5261885b4e91bc/694a220c/video/tos/alisg/tos-alisg-ve-14178-sg/okABiAGfmzeA38YlssqO4IUM53aYXgeAAW5vFf/?a=513641&bti=PDk6QC0yM2A%3D&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&br=12604&bt=6302&cs=0&ft=GAAO2Inz7ThhQBgPXq8Zmo&mime_type=video_mp4&qs=0&rc=ZTM1Omg6ODpoO2Q6N2dnOkBpamtpZms5cndoODYzODU6NEAuYGBeXzFeNi8xYDM1Li5fYSMwMjNpMmRjYi1hLS1kMy1zcw%3D%3D&vvpl=1&l=20251216130050C11DE4FBFADAE2118029&btag=e000b0000",
            "revised_prompt": "一只奔跑在草原上的狮子"
        }
    ]
}






图片测试：


出现下列错误代表请求彻底失败，图片链接有问题，或者上传图片问题
{
    "code": -2007,
    "message": "图片上传失败: 图片上传网络请求失败 (tos-d-alisg16-up.byteoversea.com): fetch failed. 请检查网络连接",
    "data": null
}


出现这个响应也代表请求彻底失败，这是账号速率限制，一个账号今日的图片生成次数消耗殆尽
{
    "code": -2001,
    "message": "[请求失败]: api rate limit (错误码: 1)",
    "data": null
}




设计表：
表1
id：雪花UUID
jimeng_account: 即梦账号
session_id: 登录状态id
xx：账号生图状态（0，1 可用，不可用）
xx：账号生视频状态（0，1 可用，不可用）
version：版本号
xx：创建时间
xx：更新时间
xx：创建人
xx：修改人
attr字段3个备用



表2
id：雪花uuid
xx：表1 ID
xx：视频链接地址 数组
xx：图片链接地址 数组
xx：视频本地地址 数组
xx：图片本地地址 数组
version：版本号
xx：创建时间
xx：更新时间
xx：创建人
xx：修改人
attr字段3个备用