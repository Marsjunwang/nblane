import './specimen.css';

const CAPTIONS = {
  title: '大标题',
  cats: '类别名',
  north: '北极星铭文',
  goals: '目标标签',
  brief: '简报行',
  latin: '拉丁+数字',
  small: '小号可读性',
};
document.querySelectorAll('.sample').forEach((el) => {
  for (const cls of Object.keys(CAPTIONS)) {
    if (el.classList.contains(cls)) {
      el.dataset.cap = cls === 'latin' && el.classList.contains('fell') ? '拉丁 · IM Fell' : CAPTIONS[cls];
      break;
    }
  }
});

document.fonts.ready.then(() => {
  window.__ready = true;
});
