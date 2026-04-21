/* Project H.O.O.D. — site JS (minimal)
   Mobile nav toggle + external link safety + active nav highlighting.
*/
(function(){
  // Mobile nav toggle
  document.addEventListener('click', function(e){
    var t = e.target.closest('.nav-toggle');
    if (!t) return;
    var links = document.querySelector('.nav-links');
    if (links) links.classList.toggle('open');
  });

  // Add rel="noopener" and target="_blank" safety to external links
  Array.prototype.forEach.call(document.querySelectorAll('a[href^="http"]'), function(a){
    if (!a.hasAttribute('target')) a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });

  // Highlight active nav item based on current path
  var path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  Array.prototype.forEach.call(document.querySelectorAll('.nav-links a'), function(a){
    var href = (a.getAttribute('href') || '').toLowerCase();
    if (!href) return;
    if (href === path || (path === 'index.html' && href === 'index.html')) {
      a.classList.add('active');
    }
  });

  // Prevent page jump on "#" placeholder links used in the prototype
  document.addEventListener('click', function(e){
    var a = e.target.closest('a[href="#"]');
    if (a) e.preventDefault();
  });
})();
